"""ABE-002: the leave-one-out criterion on real lmfit refits, with synthetic data of known model."""
from unittest.mock import patch

import numpy as np
import pytest

from entities.kinetics_sample import KineticsSampleEntity
from services.kinetics_comparison_service import get_kinetic_ml_comparison
from services.kinetics_no_linear_model_service import KineticNoLinearModel

# Same formula strings as the kinetic_model migrations.
MODELS = {
    "PFO": {"_id": 3, "name": "PFO", "formula": "qt = qe * (1 - exp(-k1 * time))",
            "parameters": {"qe": "", "k1": ""}, "truth": {"qe": 11.0, "k1": 0.012}},
    "PSO": {"_id": 2, "name": "PSO", "formula": "qt = (k2 * qe**2 * time) / (1 + k2 * qe * time)",
            "parameters": {"qe": "", "k2": ""}, "truth": {"qe": 12.0, "k2": 0.0015}},
    "IPD": {"_id": 1, "name": "IPD", "formula": "qt = kid * time**0.5 + C",
            "parameters": {"kid": "", "C": ""}, "truth": {"kid": 0.25, "C": 3.5}},
    "Elovich": {"_id": 4, "name": "Elovich", "formula": "qt = (1/beta_elo) * ln(alpha_elo * beta_elo * time + 1)",
                "parameters": {"alpha_elo": "", "beta_elo": ""}, "truth": {"alpha_elo": 0.7, "beta_elo": 0.5}},
}
# Time grid of the lab series "CA caña < 126", where Ridge took PSO data for PFO.
TIMES = np.array([0, 10, 30, 45, 60, 70, 90, 240, 360, 480, 840, 960, 1080, 1320, 1440, 1680, 1800], dtype=float)
GENERATORS = {
    "PFO": lambda t, p: p["qe"] * (1 - np.exp(-p["k1"] * t)),
    "PSO": lambda t, p: p["k2"] * p["qe"] ** 2 * t / (1 + p["k2"] * p["qe"] * t),
    "IPD": lambda t, p: p["kid"] * np.sqrt(t) + p["C"],
    "Elovich": lambda t, p: np.log(p["alpha_elo"] * p["beta_elo"] * t + 1) / p["beta_elo"],
}


def sample_of(qt):
    return KineticsSampleEntity(time=TIMES.tolist(), qt=[float(q) for q in qt])


def fitted(name, sample):
    data = MODELS[name]
    model = KineticNoLinearModel(data)
    # Seeds at the generating values of the PSO-like scale; the fit itself moves them to the optimum.
    seeds = [{"name": k, "value": v} for k, v in MODELS[name]["truth"].items()]
    model.run(sample=sample, seeds=seeds, methods={"leastsq": "Least Squares"})
    return {"model_id": data["_id"], "best": model.get_best_method(), "model": model}


def ml_pick(generator, noise=0.0, seed=2026):
    qt = GENERATORS[generator](TIMES, MODELS[generator]["truth"])
    if noise:
        qt = np.clip(qt * (1 + noise * np.random.default_rng(seed).standard_normal(TIMES.size)), 0, None)
    sample = sample_of(qt)
    result = get_kinetic_ml_comparison([fitted(name, sample) for name in MODELS], sample)
    return result["best_model"]


@pytest.mark.parametrize("generator", list(MODELS))
def test_should_pick_the_generating_model_on_noise_free_data(generator):
    """LOO-H01: PSO is the case Ridge got wrong (it picked PFO)."""
    assert ml_pick(generator) == MODELS[generator]["_id"]


def test_should_pick_pso_on_noisy_pso_data():
    """LOO-H02: one fixed-seed 5 % noise replicate; Ridge picked PFO in 14 of 20 such replicates."""
    assert ml_pick("PSO", noise=0.05) == MODELS["PSO"]["_id"]


def test_should_give_a_near_zero_error_when_the_model_generated_the_data():
    """LOO-E01"""
    sample = sample_of(GENERATORS["PFO"](TIMES, MODELS["PFO"]["truth"]))

    rmse = fitted("PFO", sample)["model"].loo_prediction_rmse(sample)

    # 1e-3 mg/g: the refits stop at lmfit's own tolerance, far below any measurement error.
    assert rmse == pytest.approx(0, abs=1e-3)


def test_should_judge_each_point_with_a_fit_that_did_not_see_it():
    """LOO-E02: on noisy data, predicting unseen points is harder than fitting them."""
    truth = MODELS["PFO"]["truth"]
    rng = np.random.default_rng(2026)
    sample = sample_of(np.clip(GENERATORS["PFO"](TIMES, truth) * (1 + 0.05 * rng.standard_normal(TIMES.size)), 0, None))
    model = fitted("PFO", sample)

    loo = model["model"].loo_prediction_rmse(sample)

    # 1 %: an in-sample error would equal the fit RMSE up to lmfit's tolerance.
    assert loo > model["best"].statistics["RMSE"] * 1.01


def test_should_return_none_when_a_refit_fails():
    """LOO-N01"""
    sample = sample_of(GENERATORS["PFO"](TIMES, MODELS["PFO"]["truth"]))
    model = fitted("PFO", sample)["model"]

    with patch.object(model.fit_strategy, "fit", side_effect=ValueError("refit diverged")):
        assert model.loo_prediction_rmse(sample) is None


def test_should_return_none_without_a_best_method():
    """LOO-N02"""
    model = KineticNoLinearModel(MODELS["PFO"])

    assert model.loo_prediction_rmse(sample_of(TIMES)) is None
