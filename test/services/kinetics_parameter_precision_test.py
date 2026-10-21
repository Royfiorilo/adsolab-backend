import math

import pytest

from entities.kinetics_sample import KineticsSampleEntity
from services.kinetics_linearization_service import _run_single_linearization
from services.kinetics_no_linear_model_service import KineticNoLinearModel
from utils import round_significant

QE, K2 = 50.0, 2.5e-5
TIMES = [0.0, 60.0, 240.0, 960.0, 2880.0, 8640.0, 17280.0, 34560.0]

PSO_MODEL = {"_id": 2, "name": "PSO", "formula": "qt = (k2 * qe**2 * time) / (1 + k2 * qe * time)",
             "parameters": {"qe": "", "k2": ""}}
PSO_LIN = {
    "linearization_id": 2,
    "name": "PSO",
    "parameters": {"x": "time", "y": "time/qt", "m": "1/qe", "b": "1/(k2 * qe**2)"},
}


def slow_pso_sample():
    return KineticsSampleEntity(
        time=list(TIMES), qt=[(K2 * QE ** 2 * t) / (1 + K2 * QE * t) for t in TIMES]
    )


def params_by_name(parameters):
    return {param["name"]: param for param in parameters}


@pytest.mark.parametrize("value, expected", [
    (1.234567e-05, 1.235e-05),
    (0.012345678, 0.01235),
    (-0.000987654, -0.0009877),
    (12.3456789, 12.3457),
])
def test_should_keep_significant_figures_when_value_is_below_one(value, expected):
    result = round_significant(value)

    # rel=1e-12: only float representation noise is tolerated.
    assert result == pytest.approx(expected, rel=1e-12)


@pytest.mark.parametrize("value", [0.0, None, True, "abc", math.inf])
def test_should_return_value_unchanged_when_it_cannot_be_rounded(value):
    assert round_significant(value) == value


def test_should_not_round_small_rate_constant_to_zero_when_fitting():
    model = KineticNoLinearModel(PSO_MODEL)

    model.run(sample=slow_pso_sample(), seeds=[{"name": "qe", "value": 40.0}, {"name": "k2", "value": 1e-4}],
              methods={"leastsq": "Least Squares"}, iterations=2000)
    k2 = params_by_name(model.get_best_method().parameters)["k2"]

    # rel=1e-3: 4 significant figures on noise-free synthetic data.
    assert k2["value"] == pytest.approx(K2, rel=1e-3)


def test_should_not_round_small_rate_constant_to_zero_when_linearizing():
    result = _run_single_linearization(slow_pso_sample(), PSO_LIN)

    k2 = params_by_name(result["parameters"])["k2"]

    assert result["status"] == "OK"
    # rel=1e-3: 4 significant figures on noise-free synthetic data.
    assert k2["value"] == pytest.approx(K2, rel=1e-3)
