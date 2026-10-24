import math

import numpy as np
import pytest

from entities.comparator import AdsorptionModelComparison, RESIDUAL_TEST_BONUS
from entities.statistics import Statistics

# Real lab series "CA caña < 126" (Cromo), Datos para trabajar.xlsx.
TIME = np.array([0, 10, 30, 45, 60, 70, 90, 240, 360, 480, 840, 960, 1080, 1320, 1440, 1680, 1800], dtype=float)
QT = np.array([0.00, 3.88, 4.98, 4.03, 4.82, 5.72, 8.00, 8.55, 9.38, 10.17, 11.30, 11.07, 11.26, 12.06, 12.22,
               11.73, 12.36])


def elovich(t, alpha=0.6589, beta=0.5179):
    return np.log(1 + alpha * beta * t) / beta


def pso(t, qe=12.4622, k2=0.00107):
    return k2 * qe ** 2 * t / (1 + k2 * qe * t)


def analysis(passes=False):
    return {"passes_normality": passes, "passes_homoscedasticity": passes, "passes_independence": passes}


def model_result(name, y_exp, y_pred, num_params=2, passes=False):
    # Same AIC definition as lmfit: n·ln(SSE/n) + 2k.
    n = len(y_exp)
    aic = n * math.log(np.sum((y_exp - y_pred) ** 2) / n) + 2 * num_params
    statistics = Statistics.all_statistics(y_exp, y_pred, num_params, aic, aic + num_params * math.log(n))
    return {"name": name, "statistics": statistics, "residuals": {"values": [], "analysis": analysis(passes)}}


def stats_result(name, rmse, aic, passes=False, adj_r2=0.95, chi_squared=0.01):
    statistics = {"RMSE": rmse, "AIC": aic, "adjust_r_squared": adj_r2, "chi_squared": chi_squared}
    return {"name": name, "statistics": statistics, "residuals": {"values": [], "analysis": analysis(passes)}}


def scores_of(*results):
    return AdsorptionModelComparison.determine_heuristic_scores_models(list(results), "name")


def test_should_add_the_residual_bonus_when_the_tests_pass():
    """HSCORE-H01"""
    passing = stats_result("passing", rmse=0.5, aic=-10.0, passes=True)
    failing = stats_result("failing", rmse=0.5, aic=-10.0, passes=False)

    scores = scores_of(passing, failing)

    # abs=1e-12: both scores are the same sum except for the bonus terms.
    assert scores["passing"] - scores["failing"] == pytest.approx(3 * RESIDUAL_TEST_BONUS, abs=1e-12)


def test_should_not_add_the_residual_bonus_when_the_tests_fail():
    """HSCORE-N01"""
    alone = stats_result("alone", rmse=0.5, aic=-10.0, passes=False)
    with_bonus = stats_result("alone", rmse=0.5, aic=-10.0, passes=True)

    assert scores_of(with_bonus)["alone"] > scores_of(alone)["alone"]


def test_should_rank_first_the_model_that_is_better_on_every_metric_when_the_other_aic_is_near_zero():
    """HSCORE-B01: real case, PSO had AIC -0.22 and won with the old 1/|AIC| term."""
    better = stats_result("elovich", rmse=0.6368, aic=-11.344, adj_r2=0.967)
    worse = stats_result("pso", rmse=0.8832, aic=-0.223, adj_r2=0.937)

    scores = scores_of(better, worse)

    assert scores["elovich"] > scores["pso"]


def test_should_keep_the_score_bounded_when_the_aic_is_exactly_zero():
    """HSCORE-B02"""
    zero_aic = stats_result("zero", rmse=0.5, aic=0.0)
    other = stats_result("other", rmse=0.5, aic=5.0)

    scores = scores_of(zero_aic, other)

    assert math.isfinite(scores["zero"])
    assert scores["zero"] <= 1.5  # max possible: 0.3 + 0.3 + 0.25 + 0.1 + 3·0.05 + rounding margin


def test_should_pick_the_same_model_when_qt_is_rescaled_to_other_units():
    """HSCORE-E01: mg/g -> g/kg is x1000; AIC shifts by the same constant for every model."""
    original = scores_of(model_result("elovich", QT, elovich(TIME)), model_result("pso", QT, pso(TIME)))
    rescaled = scores_of(model_result("elovich", QT * 1000, elovich(TIME) * 1000),
                         model_result("pso", QT * 1000, pso(TIME) * 1000))

    assert max(original, key=original.get) == max(rescaled, key=rescaled.get)
    # rel=1e-3: all_statistics rounds to 4 significant figures, so rescaled inputs round differently.
    assert rescaled["elovich"] == pytest.approx(original["elovich"], rel=1e-3)
    assert rescaled["pso"] == pytest.approx(original["pso"], rel=1e-3)


def test_should_pick_elovich_on_the_real_series():
    """HSCORE-H02: Elovich fits "CA caña < 126" better than PSO (R² 0.969 vs 0.941)."""
    scores = scores_of(model_result("elovich", QT, elovich(TIME)), model_result("pso", QT, pso(TIME)))

    assert max(scores, key=scores.get) == "elovich"


def test_should_give_a_finite_top_score_to_a_perfect_fit():
    """HSCORE-E02: RMSE = 0 must not divide by zero."""
    perfect = stats_result("perfect", rmse=0.0, aic=-100.0)
    other = stats_result("other", rmse=0.4, aic=-20.0)

    scores = scores_of(perfect, other)

    assert math.isfinite(scores["perfect"])
    assert scores["perfect"] > scores["other"]


def test_should_give_full_relative_terms_to_a_single_model():
    """HSCORE-E03: alone, a model is its own reference (RMSE ratio 1, relative likelihood 1)."""
    alone = stats_result("alone", rmse=2.0, aic=40.0, adj_r2=0.5, chi_squared=0.0)

    scores = scores_of(alone)

    # abs=1e-12: 0.3·0.5 + 0.3·1 + 0.25·1 + 0.1·1 computed exactly.
    assert scores["alone"] == pytest.approx(0.15 + 0.3 + 0.25 + 0.1, abs=1e-12)
