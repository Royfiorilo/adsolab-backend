"""ABE-005: the Elovich model as stored by its migration, fitted, compared and saved on PostgreSQL."""
import math

import pytest

from services.kinetics_investigation_service import validate_and_save_kinetic_version
from services.kinetics_linearization_service import run_kinetic_linearization
from services.kinetics_model_service import find_kinetic_models
from services.kinetics_no_linear_model_service import predict_kinetic_seeds, run_kinetic_no_linear_models
from services.kinetics_version_service import get_kinetic_version

pytestmark = pytest.mark.integration

# Same strings as test/services/kinetics_elovich_test.py, which tests them with synthetic data.
ELOVICH_FORMULA = "qt = (1/beta_elo) * ln(alpha_elo * beta_elo * time + 1)"
ELOVICH_LIN_PARAMS = {"x": "ln(time)", "y": "qt", "m": "1/beta_elo", "b": "ln(alpha_elo * beta_elo)/beta_elo"}
# Thesis fit for As(V) on bovine hydroxyapatite (García, 2018, Table III.6) converted to mg/g.
ALPHA, BETA = 1.35e-4 * 74.92, 2870 / 74.92
TIMES = [0.0, 5.0, 10.0, 15.0, 20.0, 25.0, 30.0, 60.0, 120.0, 240.0, 420.0, 600.0, 900.0, 1200.0, 1320.0]


def model_by_name(name):
    return next(m for m in find_kinetic_models() if m["name"] == name)


def thesis_sample(make_kinetic_sample, db_session):
    sample = make_kinetic_sample(time=TIMES, qt=[math.log(ALPHA * BETA * t + 1) / BETA for t in TIMES])
    # The fit closes the session; committing the savepoint keeps the sample for the save.
    db_session.commit()
    return sample


def fit(sample, *models):
    seeds = predict_kinetic_seeds({
        "kinetic_sample_id": sample.kinetic_sample_id,
        "models": [{"model": m["_id"]} for m in models],
    })
    return run_kinetic_no_linear_models({
        "kinetic_sample_id": sample.kinetic_sample_id,
        "models": [{"model": s["id"], "seeds": s["seeds"]} for s in seeds],
    })


def best_parameters(result):
    best = next(m for m in result["adjustment_methods"] if m["name"] == result["best_adjust"])
    return {p["name"]: p["value"] for p in best["parameters"]}


def test_should_store_the_elovich_model_and_its_linearization(db_session):
    """ELOI-H01"""
    model = model_by_name("Elovich")

    assert model["formula"] == ELOVICH_FORMULA
    assert set(model["parameters"]) == {"alpha_elo", "beta_elo"}
    assert "Garc" in model["description"]
    assert model["latex_formula"].startswith("q_t =")
    assert [lin["parameters"] for lin in model["linearizations"]] == [ELOVICH_LIN_PARAMS]


def test_should_run_the_stored_linearization_and_pick_it_as_best(db_session, make_kinetic_sample):
    """ELOI-H02"""
    sample = thesis_sample(make_kinetic_sample, db_session)
    model = model_by_name("Elovich")
    linearization_id = model["linearizations"][0]["linearization_id"]

    [result] = run_kinetic_linearization({
        "kinetic_sample_id": sample.kinetic_sample_id,
        "models": [{"model": model["_id"], "linearizations": [linearization_id]}],
    })

    assert result["best_result"] == linearization_id
    assert result["linearizations"][0]["dropped_points"] == 1


def test_should_fit_and_compare_elovich_with_another_model(db_session, make_kinetic_sample):
    """ELOI-H03"""
    sample = thesis_sample(make_kinetic_sample, db_session)
    elovich, pso = model_by_name("Elovich"), model_by_name("Pseudo-Segundo Orden")

    results, comparison = fit(sample, elovich, pso)

    elovich_result = next(r for r in results if r["model"] == elovich["_id"])
    params = best_parameters(elovich_result)
    # Noise-free data, but the response rounds to 4 decimals: abs 5e-5 is half of the last digit kept.
    assert params["alpha_elo"] == pytest.approx(ALPHA, abs=5e-5)
    assert params["beta_elo"] == pytest.approx(BETA, rel=1e-3)
    assert {r["model"] for r in comparison["heuristic"]["results"]} == {elovich["_id"], pso["_id"]}
    assert comparison["heuristic"]["best_model"] == elovich["_id"]


def test_should_save_and_read_back_a_version_with_elovich(db_session, make_kinetic_sample):
    """ELOI-H04"""
    sample = thesis_sample(make_kinetic_sample, db_session)
    elovich = model_by_name("Elovich")
    results, comparison = fit(sample, elovich)

    response = validate_and_save_kinetic_version(
        {"kinetic_sample_id": sample.kinetic_sample_id, "results": results, "comparison": comparison},
        sample.user_id,
    )
    db_session.expire_all()

    version = get_kinetic_version(response["kinetic_investigation_id"], response["version_id"])
    [fitted] = version.fitted_models
    assert fitted.kinetic_model_id == elovich["_id"]
    assert fitted.best_adjust == results[0]["best_adjust"]
    assert {s["name"] for s in fitted.seeds} == {"alpha_elo", "beta_elo"}
