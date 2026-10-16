"""ABE-006: the std_err each linearization returns, in kinetics and in equilibrium."""
import math
from unittest.mock import patch

import numpy as np
import pytest
from scipy.stats import linregress

from entities.kinetics_sample import KineticsSampleEntity
from entities.linearization import Linearization
from entities.sample import SampleEntity
from services.kinetics_linearization_service import _run_single_linearization
from services.linearization_service import format_linearization_result

NOISE_SEED = 11
ROUNDING = 5e-5  # the kinetic response rounds std_err to 4 decimals: half of the last digit kept
TIMES = [5.0, 10.0, 20.0, 30.0, 45.0, 60.0, 90.0, 120.0]


def noisy(values, scale):
    rng = np.random.default_rng(NOISE_SEED)
    return [v * (1 + scale * rng.standard_normal()) for v in values]


def kinetic(lin_params, qt):
    lin = {"linearization_id": 1, "name": "lin", "parameters": lin_params}
    result = _run_single_linearization(KineticsSampleEntity(time=TIMES, qt=qt), lin)
    assert result["status"] == "OK", result.get("reason")
    line = linregress(result["transformed"]["x"], result["transformed"]["y"])
    params = {p["name"]: p for p in result["parameters"]}
    return params, line


# ---------------------------------------------------------------------------
# Kinetics
# ---------------------------------------------------------------------------

def test_should_give_pso_qe_the_slope_error_times_qe_squared():
    """LSE-H01"""
    qe, k2 = 7.5, 0.02
    params, line = kinetic(
        {"x": "time", "y": "time/qt", "m": "1/qe", "b": "1/(k2 * qe**2)"},
        noisy([(k2 * qe ** 2 * t) / (1 + k2 * qe * t) for t in TIMES], 0.02),
    )

    assert params["qe"]["std_err"] == pytest.approx((1 / line.slope) ** 2 * line.stderr, abs=ROUNDING)


def test_should_include_the_slope_intercept_covariance_in_pso_k2():
    """LSE-H07: k2 = m**2 / b depends on both, so cov(m, b) = -mean(x) * var(m) changes its error"""
    qe, k2 = 7.5, 0.02
    params, line = kinetic(
        {"x": "time", "y": "time/qt", "m": "1/qe", "b": "1/(k2 * qe**2)"},
        noisy([(k2 * qe ** 2 * t) / (1 + k2 * qe * t) for t in TIMES], 0.02),
    )
    m, b = line.slope, line.intercept
    dk2_dm, dk2_db = 2 * m / b, -m ** 2 / b ** 2
    var_m, var_b = line.stderr ** 2, line.intercept_stderr ** 2
    cov_mb = -float(np.mean(TIMES)) * var_m

    expected = math.sqrt(dk2_dm ** 2 * var_m + dk2_db ** 2 * var_b + 2 * dk2_dm * dk2_db * cov_mb)

    # Without the covariance this sample gives 0.00115 instead of 0.00132, well beyond the rounding.
    assert params["k2"]["std_err"] == pytest.approx(expected, abs=ROUNDING)


def test_should_give_pfo_qe_the_intercept_error_times_qe_and_k1_the_slope_error():
    """LSE-H02"""
    qe, k1 = 7.5, 0.03
    params, line = kinetic(
        {"x": "time", "y": "ln(qe - qt)", "m": "-k1", "b": "ln(qe)"},
        noisy([qe * (1 - math.exp(-k1 * t)) for t in TIMES], 0.01),
    )

    # The transform uses qe = max(qt), so the solved qe is exp(intercept), not the true 7.5.
    assert params["qe"]["std_err"] == pytest.approx(math.exp(line.intercept) * line.intercept_stderr, abs=ROUNDING)
    assert params["k1"]["std_err"] == pytest.approx(line.stderr, abs=ROUNDING)


def test_should_give_elovich_beta_the_slope_error_times_beta_squared():
    """LSE-H03"""
    alpha, beta = 0.0101, 38.31
    params, line = kinetic(
        {"x": "ln(time)", "y": "qt", "m": "1/beta_elo", "b": "ln(alpha_elo * beta_elo)/beta_elo"},
        noisy([math.log(alpha * beta * t + 1) / beta for t in TIMES], 0.02),
    )

    assert params["beta_elo"]["std_err"] > 0
    assert params["beta_elo"]["std_err"] == pytest.approx((1 / line.slope) ** 2 * line.stderr, abs=ROUNDING)


def test_should_keep_the_intraparticle_errors_equal_to_the_line_errors():
    """LSE-H04"""
    params, line = kinetic(
        {"x": "time**0.5", "y": "qt", "m": "kid", "b": "C"},
        noisy([1.2 * math.sqrt(t) + 0.5 for t in TIMES], 0.02),
    )

    assert params["kid"]["std_err"] == pytest.approx(line.stderr, abs=ROUNDING)
    assert params["C"]["std_err"] == pytest.approx(line.intercept_stderr, abs=ROUNDING)


# ---------------------------------------------------------------------------
# Equilibrium
# ---------------------------------------------------------------------------

CE = [0.05, 0.1, 0.2, 0.4, 0.8, 1.6, 3.2]


def equilibrium(name, formula, lin_params, qe):
    sample = SampleEntity(ce=CE, qe=qe, sample_id=1, temperature=298, measure_unit="mg",
                          adsorbate_id=1, adsorbent_id=1)
    linearization = Linearization(linearization_id=1, name=name, formula=formula, description="",
                                  parameters=lin_params, latex_formula="", model_id=1)
    result = linearization.run(sample, {})
    values, std_errs = result["params_info"][0], result["params_info"][1]
    return values, std_errs, linregress(result["x"], result["y"])


def test_should_give_hanes_woolf_qmax_the_slope_error_times_qmax_squared():
    """LSE-H05"""
    qmax, k = 30.0, 2.5
    values, std_errs, line = equilibrium(
        "HaneseWoolf Linearization", "ce/qe = (1/qmax) * ce + 1 / (qmax * k)",
        {"x": "ce", "y": "ce/qe", "m": "1/qmax", "b": "1/(qmax * k)"},
        noisy([qmax * k * c / (1 + k * c) for c in CE], 0.02),
    )

    # rel 1e-9: the equilibrium entity returns unrounded errors.
    assert std_errs["qmax"] == pytest.approx(values["qmax"] ** 2 * line.stderr, rel=1e-9)


def test_should_include_the_slope_intercept_covariance_in_hanes_woolf_k():
    """LSE-H08: k = m / b depends on both slope and intercept"""
    qmax, k = 30.0, 2.5
    values, std_errs, line = equilibrium(
        "HaneseWoolf Linearization", "ce/qe = (1/qmax) * ce + 1 / (qmax * k)",
        {"x": "ce", "y": "ce/qe", "m": "1/qmax", "b": "1/(qmax * k)"},
        noisy([qmax * k * c / (1 + k * c) for c in CE], 0.02),
    )
    m, b = line.slope, line.intercept
    dk_dm, dk_db = 1 / b, -m / b ** 2
    var_m, var_b = line.stderr ** 2, line.intercept_stderr ** 2
    cov_mb = -float(np.mean(CE)) * var_m

    expected = math.sqrt(dk_dm ** 2 * var_m + dk_db ** 2 * var_b + 2 * dk_dm * dk_db * cov_mb)

    assert std_errs["k"] == pytest.approx(expected, rel=1e-9)


def test_should_give_freundlich_kf_and_nf_their_delta_method_errors():
    """LSE-H06"""
    kf, nf = 4.0, 2.5
    values, std_errs, line = equilibrium(
        "Freundlich Linearization", "log(qe) = log(kf) + 1/nf * log(ce)",
        {"x": "log(ce)", "y": "log(qe)", "m": "1 / nf", "b": "log(kf)"},
        noisy([kf * c ** (1 / nf) for c in CE], 0.02),
    )

    assert std_errs["kf"] == pytest.approx(values["kf"] * line.intercept_stderr, rel=1e-9)
    assert std_errs["nf"] == pytest.approx(values["nf"] ** 2 * line.stderr, rel=1e-9)


# ---------------------------------------------------------------------------
# An error that cannot be computed is null, and the linearization is still OK
# ---------------------------------------------------------------------------

def test_should_return_a_null_std_err_and_status_ok_in_kinetics():
    """LSE-N01"""
    lin = {"linearization_id": 1, "name": "lin", "parameters": {"x": "time**0.5", "y": "qt", "m": "kid", "b": "C"}}
    data = KineticsSampleEntity(time=TIMES, qt=[1.2 * math.sqrt(t) + 0.5 for t in TIMES])

    with patch("services.kinetics_linearization_service.propagate_std_errors",
               return_value={"kid": None, "C": None}):
        result = _run_single_linearization(data, lin)

    assert result["status"] == "OK"
    assert [p["std_err"] for p in result["parameters"]] == [None, None]
    assert {p["name"]: p["value"] for p in result["parameters"]} == {"kid": 1.2, "C": 0.5}


def test_should_return_a_null_std_err_in_equilibrium():
    """LSE-N02"""
    result = format_linearization_result(
        name="lin", id=1, x=[1.0], y=[2.0], slope=0.1, intercept=0.2, vars=["qmax"],
        params_info=({"qmax": 30.0}, {"qmax": None}), statistics={"r_squared": 0.99},
    )

    assert result["parameters"] == [{"name": "qmax", "value": 30.0, "std_err": None}]
