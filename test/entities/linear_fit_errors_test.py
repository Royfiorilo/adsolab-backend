"""ABE-006: standard errors of parameters solved from a fitted line (delta method)."""
import math

import numpy as np
import pytest
from scipy.stats import linregress
from sympy import sympify

from entities.linear_fit_errors import line_covariance, propagate_std_errors

MC_DRAWS = 20000
MC_SEED = 7
COV = np.array([[0.004 ** 2, -1.5e-5], [-1.5e-5, 0.05 ** 2]])  # a valid covariance with m-b correlation
VAR_M, COV_MB, VAR_B = COV[0, 0], COV[0, 1], COV[1, 1]


def errors(m, b, params, covariance=COV):
    return propagate_std_errors(sympify(m), sympify(b), params, covariance)


# ---------------------------------------------------------------------------
# Covariance of the line
# ---------------------------------------------------------------------------

def test_should_give_the_same_covariance_as_numpy_for_a_least_squares_line():
    """LFE-H01"""
    rng = np.random.default_rng(MC_SEED)
    x = np.linspace(1.0, 10.0, 12)
    y = 0.3 * x + 2.0 + rng.normal(0, 0.2, x.size)

    covariance = line_covariance(linregress(x, y), x)

    _, expected = np.polyfit(x, y, 1, cov=True)
    # rel 1e-9: both are the same closed form, only float rounding differs.
    np.testing.assert_allclose(covariance, expected, rtol=1e-9)


# ---------------------------------------------------------------------------
# Closed forms of the delta method
# ---------------------------------------------------------------------------

def test_should_keep_the_errors_of_slope_and_intercept_when_they_are_the_parameters():
    """LFE-H02 (intraparticle: m = kid, b = C)"""
    result = errors("kid", "C", {"kid": 1.2, "C": 0.5})

    assert result["kid"] == pytest.approx(math.sqrt(VAR_M), rel=1e-12)
    assert result["C"] == pytest.approx(math.sqrt(VAR_B), rel=1e-12)


def test_should_scale_the_slope_error_by_qe_squared_for_qe_equal_one_over_m():
    """LFE-H03 (PSO qe; Hanes-Woolf qmax and Elovich beta have the same form)"""
    qe = 7.5

    result = errors("1/qe", "1/(k2 * qe**2)", {"qe": qe, "k2": 0.02})

    assert result["qe"] == pytest.approx(qe ** 2 * math.sqrt(VAR_M), rel=1e-12)


def test_should_combine_slope_intercept_and_covariance_for_k2():
    """LFE-H04 (PSO k2 = m**2 / b)"""
    qe, k2 = 7.5, 0.02
    m, b = 1 / qe, 1 / (k2 * qe ** 2)
    dk2_dm, dk2_db = 2 * m / b, -m ** 2 / b ** 2

    result = errors("1/qe", "1/(k2 * qe**2)", {"qe": qe, "k2": k2})

    expected = math.sqrt(dk2_dm ** 2 * VAR_M + dk2_db ** 2 * VAR_B + 2 * dk2_dm * dk2_db * COV_MB)
    assert result["k2"] == pytest.approx(expected, rel=1e-12)


def test_should_scale_the_intercept_error_by_qe_for_qe_equal_exp_b():
    """LFE-H05 (PFO: m = -k1, b = ln(qe); Freundlich kf has the same form)"""
    qe = 7.5

    result = errors("-k1", "ln(qe)", {"k1": 0.15, "qe": qe})

    assert result["qe"] == pytest.approx(qe * math.sqrt(VAR_B), rel=1e-12)
    assert result["k1"] == pytest.approx(math.sqrt(VAR_M), rel=1e-12)


# ---------------------------------------------------------------------------
# Not computable
# ---------------------------------------------------------------------------

def test_should_return_none_when_the_jacobian_is_singular():
    """LFE-N01: m and b depend on x and y only through x*y"""
    assert errors("x*y", "2*x*y", {"x": 1.0, "y": 2.0}) == {"x": None, "y": None}


@pytest.mark.parametrize("m, b, params", [
    ("a", "1", {"a": 1.0}),
    ("a*c", "b", {"a": 1.0, "b": 2.0, "c": 3.0}),
])
def test_should_return_none_when_the_line_does_not_give_two_unknowns(m, b, params):
    """LFE-N02"""
    assert set(errors(m, b, params).values()) == {None}


# ---------------------------------------------------------------------------
# Monte Carlo: the propagated error matches the spread over many noisy lines
# ---------------------------------------------------------------------------

def monte_carlo_lines(x, m, b, sigma):
    rng = np.random.default_rng(MC_SEED)
    y = m * x + b + rng.normal(0, sigma, (MC_DRAWS, x.size))
    xc = x - x.mean()
    slopes = (y - y.mean(axis=1, keepdims=True)) @ xc / (xc @ xc)
    intercepts = y.mean(axis=1) - slopes * x.mean()
    design = np.column_stack([x, np.ones_like(x)])
    covariance = sigma ** 2 * np.linalg.inv(design.T @ design)
    return slopes, intercepts, covariance


@pytest.mark.parametrize("label, x, params, m, b, invert, sigma", [
    (
        "pso", np.array([5.0, 10.0, 20.0, 30.0, 45.0, 60.0, 90.0]), {"qe": 7.5, "k2": 0.02},
        "1/qe", "1/(k2 * qe**2)",
        lambda m, b: {"qe": 1 / m, "k2": m ** 2 / b}, 0.02,
    ),
    (
        "elovich", np.log([5.0, 10.0, 30.0, 60.0, 120.0, 420.0, 900.0, 1320.0]),
        {"alpha_elo": 0.0101, "beta_elo": 38.31}, "1/beta_elo", "ln(alpha_elo * beta_elo)/beta_elo",
        lambda m, b: {"beta_elo": 1 / m, "alpha_elo": m * np.exp(b / m)}, 0.001,
    ),
])
def test_should_match_the_spread_of_the_solved_parameters_over_noisy_lines(label, x, params, m, b, invert, sigma):
    """LFE-H06"""
    m_value = float(sympify(m).subs(params))
    b_value = float(sympify(b).subs(params))
    slopes, intercepts, covariance = monte_carlo_lines(x, m_value, b_value, sigma)
    empirical = {name: float(np.std(values)) for name, values in invert(slopes, intercepts).items()}

    propagated = errors(m, b, params, covariance)

    # rel 5 %: 20000 draws give ~0.5 % sampling error; the rest is the delta method's linearization.
    for name in params:
        assert propagated[name] == pytest.approx(empirical[name], rel=0.05), f"{label} {name}"
