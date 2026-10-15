"""ABE-005: Elovich model, checked against the reference (García, 2018, FIUBA) with synthetic data."""
import math

import numpy as np
import pytest
from scipy.integrate import solve_ivp

from entities.formula import Formula
from entities.kinetic_parameters import POSITIVE_PARAM_MIN
from entities.kinetics_sample import KineticsSampleEntity
from entities.no_linear_model import MIN_PARAM_VALUE
from services.kinetics_linearization_service import _run_single_linearization
from services.kinetics_no_linear_model_service import KineticNoLinearModel, calculate_kinetic_seeds

# Same strings as migration 20261015000001 (the integration test checks the stored rows).
ELOVICH_FORMULA = "qt = (1/beta_elo) * ln(alpha_elo * beta_elo * time + 1)"
ELOVICH_MODEL = {
    "_id": 99,
    "name": "Elovich",
    "formula": ELOVICH_FORMULA,
    "parameters": {"alpha_elo": "", "beta_elo": ""},
}
ELOVICH_LIN = {
    "linearization_id": 99,
    "name": "Linealización Elovich",
    "parameters": {"x": "ln(time)", "y": "qt", "m": "1/beta_elo", "b": "ln(alpha_elo * beta_elo)/beta_elo"},
}
PFO_MODEL = {
    "_id": 98,
    "name": "PFO",
    "formula": "qt = qe * (1 - exp(-k1 * time))",
    "parameters": {"k1": "", "qe": ""},
}
LOCAL_METHODS = {"leastsq": "", "nelder": "", "cobyla": ""}

# Thesis fit for As(V) on bovine hydroxyapatite (Table III.6), in mmol/g and min.
THESIS_ALPHA, THESIS_BETA = 1.35e-4, 2870.0
AS_MOLAR_MASS = 74.92  # g/mol, to express the same fit in mg/g, the app's unit
ALPHA, BETA = THESIS_ALPHA * AS_MOLAR_MASS, THESIS_BETA / AS_MOLAR_MASS
# Contact times of the thesis kinetic runs (Figure III.14), up to 24 h.
TIMES = [0.0, 5.0, 10.0, 15.0, 20.0, 25.0, 30.0, 60.0, 120.0, 240.0, 420.0, 600.0, 900.0, 1200.0, 1320.0]
NOISE_SEED = 42


def elovich(alpha, beta, t):
    return math.log(alpha * beta * t + 1) / beta


def sample(alpha=ALPHA, beta=BETA, times=TIMES, noise=0.0):
    rng = np.random.default_rng(NOISE_SEED)
    qt = [elovich(alpha, beta, t) * (1 + noise * rng.standard_normal()) for t in times]
    return KineticsSampleEntity(time=list(times), qt=qt)


def best_params(model_data, kinetic_sample, seeds=None):
    model = KineticNoLinearModel(model_data)
    model.run(kinetic_sample, seeds or calculate_kinetic_seeds(kinetic_sample, model_data), LOCAL_METHODS)
    best = model.get_best_method()
    assert best is not None, "no method succeeded"
    return best.raw_result.params


def seeds_by_name(kinetic_sample):
    return {s["name"]: s["value"] for s in calculate_kinetic_seeds(kinetic_sample, ELOVICH_MODEL)}


# ---------------------------------------------------------------------------
# Formula
# ---------------------------------------------------------------------------

def test_should_match_the_integral_of_the_elovich_rate_law():
    """ELO-H01"""
    rate = lambda t, q: [THESIS_ALPHA * math.exp(-THESIS_BETA * q[0])]
    numeric = solve_ivp(rate, (0, TIMES[-1]), [0.0], t_eval=TIMES, rtol=1e-10, atol=1e-14)

    closed = Formula(ELOVICH_FORMULA).apply(alpha_elo=THESIS_ALPHA, beta_elo=THESIS_BETA, time=np.array(TIMES))

    # rtol 1e-6: bounded by the ODE solver tolerance, not by the formula.
    np.testing.assert_allclose(closed, numeric.y[0], rtol=1e-6, atol=1e-12)


def test_should_start_at_zero_adsorbed_at_time_zero():
    """ELO-E01"""
    assert Formula(ELOVICH_FORMULA).apply(alpha_elo=ALPHA, beta_elo=BETA, time=0.0) == 0.0


# ---------------------------------------------------------------------------
# Non-linear fit
# ---------------------------------------------------------------------------

def test_should_recover_alpha_and_beta_from_noise_free_data_starting_at_the_default_seeds():
    """ELO-H02"""
    params = best_params(ELOVICH_MODEL, sample())

    # rel 1e-4: the fit stops at lmfit's own tolerance.
    assert params["alpha_elo"].value == pytest.approx(ALPHA, rel=1e-4)
    assert params["beta_elo"].value == pytest.approx(BETA, rel=1e-4)


def test_should_recover_alpha_and_beta_within_ten_percent_with_two_percent_noise():
    """ELO-H03"""
    params = best_params(ELOVICH_MODEL, sample(noise=0.02))

    # rel 0.1: 2 % multiplicative noise on 14 points moves the optimum (measured 6 % on alpha, 2 % on beta).
    assert params["alpha_elo"].value == pytest.approx(ALPHA, rel=0.1)
    assert params["beta_elo"].value == pytest.approx(BETA, rel=0.1)


def test_should_recover_the_thesis_values_in_mmol_per_gram():
    """ELO-B01"""
    params = best_params(ELOVICH_MODEL, sample(alpha=THESIS_ALPHA, beta=THESIS_BETA))

    # alpha is 1.35e-4, so the positive lower bound must sit far below it; rel 1e-4 as in ELO-H02.
    assert params["alpha_elo"].value == pytest.approx(THESIS_ALPHA, rel=1e-4)
    assert params["beta_elo"].value == pytest.approx(THESIS_BETA, rel=1e-4)


def test_should_never_evaluate_a_non_positive_alpha_or_beta_even_from_zero_seeds():
    """ELO-N01"""
    model = KineticNoLinearModel(ELOVICH_MODEL)
    evaluated = []
    original = model.fit_strategy.model.func

    def spy(time, alpha_elo, beta_elo):
        evaluated.append((alpha_elo, beta_elo))
        return original(alpha_elo, beta_elo, time)

    model.fit_strategy.model.func = spy
    zero_seeds = [{"name": "alpha_elo", "value": 0.0}, {"name": "beta_elo", "value": 0.0}]

    model.run(sample(), zero_seeds, LOCAL_METHODS)

    assert evaluated
    assert min(min(a, b) for a, b in evaluated) >= POSITIVE_PARAM_MIN


def test_should_bound_alpha_and_beta_away_from_zero_and_keep_the_other_models_bounds():
    """ELO-H04"""
    elovich_params = best_params(ELOVICH_MODEL, sample())
    pfo_sample = KineticsSampleEntity(time=TIMES[1:], qt=[7.5 * (1 - math.exp(-0.05 * t)) for t in TIMES[1:]])
    pfo_params = best_params(PFO_MODEL, pfo_sample)

    assert elovich_params["alpha_elo"].min == POSITIVE_PARAM_MIN
    assert elovich_params["beta_elo"].min == POSITIVE_PARAM_MIN
    assert pfo_params["k1"].min == 0
    assert pfo_params["qe"].min == MIN_PARAM_VALUE


# ---------------------------------------------------------------------------
# Default seeds
# ---------------------------------------------------------------------------

def test_should_seed_alpha_with_the_first_rate_and_beta_with_the_inverse_of_max_qt():
    """ELO-H05"""
    data = sample()

    seeds = seeds_by_name(data)

    # abs 1e-6: seeds are rounded to 6 decimal places.
    assert seeds["alpha_elo"] == pytest.approx(data.qt[1] / data.time[1], abs=1e-6)
    assert seeds["beta_elo"] == pytest.approx(1 / max(data.qt), abs=1e-6)


def test_should_take_the_earliest_time_when_the_sample_is_unsorted():
    """ELO-E02"""
    data = KineticsSampleEntity(time=[60.0, 10.0, 0.0, 30.0], qt=[0.08, 0.04, 0.0, 0.06])

    assert seeds_by_name(data)["alpha_elo"] == pytest.approx(0.004)


def test_should_skip_points_without_adsorption_when_seeding_alpha():
    """ELO-E03"""
    data = KineticsSampleEntity(time=[0.0, 5.0, 10.0, 20.0], qt=[0.0, 0.0, 0.05, 0.08])

    assert seeds_by_name(data)["alpha_elo"] == pytest.approx(0.005)


def test_should_fall_back_to_positive_seeds_when_nothing_was_adsorbed():
    """ELO-E04"""
    data = KineticsSampleEntity(time=[0.0, 5.0, 10.0], qt=[0.0, 0.0, 0.0])

    assert seeds_by_name(data) == {"alpha_elo": 1.0, "beta_elo": 1.0}


# ---------------------------------------------------------------------------
# Linearization (qt vs ln t)
# ---------------------------------------------------------------------------

def test_should_linearize_and_drop_time_zero():
    """ELO-H06"""
    result = _run_single_linearization(sample(), ELOVICH_LIN)

    assert result["status"] == "OK"
    assert result["dropped_points"] == 1
    assert all(p["value"] > 0 for p in result["parameters"])


def test_should_recover_the_parameters_where_the_linear_approximation_holds():
    """ELO-H07"""
    alpha, beta = 50.0, 2.0  # alpha * beta * t >= 1000 for every t >= 10, so the dropped + 1 is negligible
    data = sample(alpha=alpha, beta=beta, times=[10.0, 20.0, 40.0, 80.0, 160.0, 320.0])

    params = {p["name"]: p["value"] for p in _run_single_linearization(data, ELOVICH_LIN)["parameters"]}

    # rel 5e-3: the dropped + 1 still shifts ln(qt) by ~1/(alpha*beta*t) = 1e-3 at t = 10 (measured 0.2 %).
    assert params["alpha_elo"] == pytest.approx(alpha, rel=5e-3)
    assert params["beta_elo"] == pytest.approx(beta, rel=5e-3)


def test_should_report_an_error_when_the_line_slopes_down():
    """ELO-N02"""
    data = KineticsSampleEntity(time=[5.0, 10.0, 20.0, 40.0], qt=[0.20, 0.15, 0.10, 0.05])

    result = _run_single_linearization(data, ELOVICH_LIN)

    assert result["status"] == "ERROR"
    assert "must be positive" in result["reason"]


def test_should_solve_a_line_that_made_sympy_hang_with_exact_rationals():
    """ELO-E05"""
    # These points give slope 0.029446 and intercept 0.002363: solve() with rationals never returned.
    xs, ys = [1.6, 2.3, 3.0, 4.0, 5.0], [0.05, 0.07, 0.09, 0.12, 0.15]
    data = KineticsSampleEntity(time=[math.exp(x) for x in xs], qt=ys)

    result = _run_single_linearization(data, ELOVICH_LIN)

    assert result["status"] == "OK"
