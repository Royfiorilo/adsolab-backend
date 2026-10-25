import warnings

import numpy as np
from scipy.stats import ConstantInputWarning

from entities.statistics import Statistics

# Real time grid of the lab series "CA caña < 126" and a PSO-shaped fitted curve over it.
TIMES = np.array([0, 10, 30, 45, 60, 70, 90, 240, 360, 480, 840, 960, 1080, 1320, 1440, 1680, 1800], dtype=float)
LOG_TIMES = np.geomspace(1, 1800, 24)
REPLICATES = 1000


def pso_curve(t):
    return 0.0015 * 12 ** 2 * t / (1 + 0.0015 * 12 * t)


def rejection_rate(make_residuals, fitted, seed=2026):
    rng = np.random.default_rng(seed)
    rejected = 0
    for _ in range(REPLICATES):
        analysis = Statistics.check_residuals(make_residuals(rng), fitted)
        rejected += analysis["passes_homoscedasticity"] is False
    return rejected / REPLICATES


def test_should_reject_homoscedastic_residuals_only_at_about_the_nominal_rate():
    """HOMO-H01: the old check (Levene vs a constant vector) rejected 100 % of these."""
    fitted = pso_curve(TIMES)

    rate = rejection_rate(lambda rng: rng.normal(0, 0.5, TIMES.size), fitted)

    # 2-9 %: nominal 5 % plus the sampling error of 1000 replicates and the test's small-sample size.
    assert 0.02 <= rate <= 0.09


def test_should_reject_residuals_whose_spread_grows_with_the_fit_far_more_often():
    """HOMO-N01"""
    fitted = pso_curve(LOG_TIMES)

    rate = rejection_rate(lambda rng: rng.normal(0, 0.03 + 0.08 * fitted), fitted)

    # Measured at about 98 %; 80 % leaves room for a different but valid test implementation.
    assert rate >= 0.8


def test_should_pass_a_clearly_homoscedastic_sample():
    """HOMO-H02"""
    fitted = pso_curve(TIMES)
    residuals = np.random.default_rng(7).normal(0, 0.5, TIMES.size)

    analysis = Statistics.check_residuals(residuals, fitted)

    assert analysis["passes_homoscedasticity"] is True
    assert 0.05 < analysis["homoscedasticity_pvalue"] <= 1


def test_should_report_not_evaluated_when_there_are_too_few_points():
    """HOMO-B01: 4 points, one below the minimum."""
    analysis = Statistics.check_residuals(np.array([0.1, -0.2, 0.15, -0.05]), np.array([1.0, 2.0, 3.0, 4.0]))

    assert analysis["passes_homoscedasticity"] is None
    assert analysis["homoscedasticity_pvalue"] is None


def test_should_evaluate_from_the_minimum_number_of_points():
    """HOMO-B02: 5 points, the minimum."""
    analysis = Statistics.check_residuals(np.array([0.1, -0.2, 0.15, -0.05, 0.12]),
                                          np.array([1.0, 2.0, 3.0, 4.0, 5.0]))

    assert analysis["passes_homoscedasticity"] in (True, False)


def test_should_report_not_evaluated_when_the_fitted_values_are_constant():
    """HOMO-E01: no variation along the fit, so a trend in the spread cannot exist."""
    with warnings.catch_warnings():
        # The guard must stop before Spearman, which warns on constant input.
        warnings.simplefilter("error", ConstantInputWarning)
        analysis = Statistics.check_residuals(np.array([0.1, -0.2, 0.15, -0.05, 0.12, -0.1]), np.full(6, 3.0))

    assert analysis["passes_homoscedasticity"] is None


def test_should_report_not_evaluated_for_a_perfect_fit():
    """HOMO-E02: all residuals zero."""
    with warnings.catch_warnings():
        warnings.simplefilter("error", ConstantInputWarning)
        analysis = Statistics.check_residuals(np.zeros(6), np.arange(6, dtype=float))

    assert analysis["passes_homoscedasticity"] is None
