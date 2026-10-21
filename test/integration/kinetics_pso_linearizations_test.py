"""The four PSO linear forms (Tran et al., 2017) as stored by the migrations, on PostgreSQL."""
import pytest

from services.kinetics_linearization_service import run_kinetic_linearization
from services.kinetics_model_service import find_kinetic_models

pytestmark = pytest.mark.integration

QE, K2 = 7.5, 0.02
TIMES = [0.0, 5.0, 10.0, 20.0, 30.0, 45.0, 60.0]
PSO_AXES = {("time", "time/qt"), ("1/time", "1/qt"), ("qt/time", "qt"), ("qt", "qt/time")}


def pso_model():
    return next(model for model in find_kinetic_models() if model["name"] == "Pseudo-Segundo Orden")


def test_should_store_the_four_linear_forms_of_pso(db_session):
    linearizations = pso_model()["linearizations"]

    assert {(lin["parameters"]["x"], lin["parameters"]["y"]) for lin in linearizations} == PSO_AXES


def test_should_recover_pso_parameters_with_every_stored_linear_form(db_session, make_kinetic_sample):
    sample = make_kinetic_sample(time=TIMES, qt=[(K2 * QE ** 2 * t) / (1 + K2 * QE * t) for t in TIMES])
    model = pso_model()

    [result] = run_kinetic_linearization({
        "kinetic_sample_id": sample.kinetic_sample_id,
        "models": [{"model": model["_id"], "linearizations": [lin["linearization_id"] for lin in model["linearizations"]]}],
    })

    assert len(result["linearizations"]) == 4
    for linearization in result["linearizations"]:
        params = {param["name"]: param["value"] for param in linearization["parameters"]}
        assert linearization["status"] == "OK"
        # rel=1e-3: noise-free data, limited by the 4-decimal rounding of the transformed points.
        assert params["qe"] == pytest.approx(QE, rel=1e-3)
        assert params["k2"] == pytest.approx(K2, rel=1e-3)
