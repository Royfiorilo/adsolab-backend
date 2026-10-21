import math

import pytest

from entities.kinetics_sample import KineticsSampleEntity
from services.kinetics_linearization_service import _run_single_linearization

QE, K2 = 7.5, 0.02
K1 = 0.15
TIMES = [0.0, 5.0, 10.0, 20.0, 30.0, 45.0, 60.0]

# Same parameter strings as db/migrations/20261021000001_add_pso_linearizations.sql.
PSO_TYPE_2 = {"x": "1/time", "y": "1/qt", "m": "1/(k2 * qe**2)", "b": "1/qe"}
PSO_TYPE_3 = {"x": "qt/time", "y": "qt", "m": "-1/(k2 * qe)", "b": "qe"}
PSO_TYPE_4 = {"x": "qt", "y": "qt/time", "m": "-k2 * qe", "b": "k2 * qe**2"}
PFO = {"x": "time", "y": "ln(qe - qt)", "m": "-k1", "b": "ln(qe)"}


def pso_sample():
    return KineticsSampleEntity(time=list(TIMES), qt=[(K2 * QE ** 2 * t) / (1 + K2 * QE * t) for t in TIMES])


def pfo_sample():
    return KineticsSampleEntity(time=list(TIMES), qt=[QE * (1 - math.exp(-K1 * t)) for t in TIMES])


def linearization(parameters):
    return {"linearization_id": 1, "name": "test", "parameters": parameters}


def params_by_name(result):
    return {param["name"]: param["value"] for param in result["parameters"]}


@pytest.mark.parametrize("parameters", [PSO_TYPE_2, PSO_TYPE_3, PSO_TYPE_4], ids=["type2", "type3", "type4"])
def test_should_recover_pso_parameters_when_using_each_linear_form(parameters):
    result = _run_single_linearization(pso_sample(), linearization(parameters))

    params = params_by_name(result)
    assert result["status"] == "OK"
    # rel=1e-3: noise-free data, limited by the 4-decimal rounding of the transformed points.
    assert params["qe"] == pytest.approx(QE, rel=1e-3)
    assert params["k2"] == pytest.approx(K2, rel=1e-3)
    assert result["dropped_points"] == 1


def test_should_reject_pfo_when_given_qe_is_below_the_largest_qt():
    sample = pfo_sample()

    result = _run_single_linearization(sample, linearization(PFO), {"qe": max(sample.qt) * 0.9})

    assert result["status"] == "ERROR"
    assert "largest measured qt" in result["reason"]


def test_should_accept_pfo_when_given_qe_equals_the_largest_qt():
    sample = pfo_sample()

    result = _run_single_linearization(sample, linearization(PFO), {"qe": max(sample.qt)})

    assert result["status"] == "OK"
