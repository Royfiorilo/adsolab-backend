import math
import unittest
from unittest.mock import MagicMock

from entities.kinetics_sample import KineticsSampleEntity
from services.kinetics_comparison_service import (
    determine_kinetic_heuristic_scores,
    get_kinetic_comparison,
    get_kinetic_ml_comparison,
)

QE, K1, K2 = 7.5, 0.15, 0.02
TIMES = [0.0, 5.0, 10.0, 20.0, 30.0, 45.0, 60.0]
EXTENDED_TIMES = [t / 2 for t in range(0, 121)]


def sample():
    return KineticsSampleEntity(
        time=list(TIMES), qt=[QE * (1 - math.exp(-K1 * t)) for t in TIMES]
    )


def statistics(r_squared, rmse, aic):
    return {
        "r_squared": r_squared,
        "adjust_r_squared": r_squared - 0.01,
        "chi_squared": 0.004,
        "adjust_chi_squeared": 0.0002,
        "RMSE": rmse,
        "SSE": rmse ** 2,
        "HYBRID": 3.6,
        "AIC": aic,
        "BIC": aic + 2,
    }


def residuals():
    return {
        "values": [0.01, -0.02, 0.015, -0.005, 0.02, -0.01, 0.004],
        "analysis": {
            "normality_pvalue": 0.7,
            "homoscedasticity_pvalue": 0.4,
            "durbin_watson": 2.0,
            "passes_normality": 1,
            "passes_homoscedasticity": 1,
            "passes_independence": 1,
        },
    }


def fitted_model(model_id, qt_pred, extended_pred, stats=None, best=True, loo_rmse=0.1):
    method = MagicMock()
    method.statistics = stats or statistics(0.99, 0.05, -20.0)
    method.residuals = residuals()
    method.transformed = {"x": list(EXTENDED_TIMES), "y": list(extended_pred), "qt_pred": list(qt_pred)}

    model = MagicMock()
    model.get_best_method.return_value = method if best else None
    model.loo_prediction_rmse.return_value = loo_rmse
    return model, model_id


def pfo_predictions(qe=QE, k1=K1):
    return (
        [qe * (1 - math.exp(-k1 * t)) for t in TIMES],
        [qe * (1 - math.exp(-k1 * t)) for t in EXTENDED_TIMES],
    )


def pso_predictions(qe=QE, k2=K2):
    return (
        [(k2 * qe ** 2 * t) / (1 + k2 * qe * t) for t in TIMES],
        [(k2 * qe ** 2 * t) / (1 + k2 * qe * t) for t in EXTENDED_TIMES],
    )


class TestGetKineticComparison(unittest.TestCase):
    def test_should_return_empty_comparison_when_no_models_were_fitted(self):
        self.assertEqual(get_kinetic_comparison([], sample()), {"heuristic": None, "ml": None})

    def test_should_return_empty_comparison_when_no_model_has_a_best_method(self):
        qt_pred, extended = pfo_predictions()

        result = get_kinetic_comparison([fitted_model(3, qt_pred, extended, best=False)], sample())

        self.assertEqual(result, {"heuristic": None, "ml": None})

    def test_should_ignore_models_without_a_best_method(self):
        qt_pred, extended = pfo_predictions()
        models = [
            fitted_model(3, qt_pred, extended),
            fitted_model(2, *pso_predictions(), best=False),
        ]

        result = get_kinetic_comparison(models, sample())

        self.assertEqual([r["model"] for r in result["heuristic"]["results"]], [3])
        self.assertEqual([r["model"] for r in result["ml"]["results"]], [3])

    def test_should_build_both_heuristic_and_ml_blocks(self):
        models = [
            fitted_model(3, *pfo_predictions()),
            fitted_model(2, *pso_predictions()),
        ]

        result = get_kinetic_comparison(models, sample())

        self.assertIn("best_model", result["heuristic"])
        self.assertEqual(len(result["heuristic"]["results"]), 2)
        self.assertEqual(result["ml"]["criterion"], "loo_cv")
        self.assertIn("best_model", result["ml"])
        self.assertEqual(len(result["ml"]["results"]), 2)


class TestDetermineKineticHeuristicScores(unittest.TestCase):
    def test_should_pick_the_model_with_the_better_statistics(self):
        qt_pred, extended = pfo_predictions()
        good = {"model_id": 3, "best": fitted_model(3, qt_pred, extended)[0].get_best_method()}
        bad_model = fitted_model(2, *pso_predictions(), stats=statistics(0.55, 1.9, 40.0))[0]
        bad = {"model_id": 2, "best": bad_model.get_best_method()}

        scores, best = determine_kinetic_heuristic_scores([good, bad])

        self.assertEqual(best, 3)
        self.assertGreater(scores[3], scores[2])


class TestGetKineticMlComparison(unittest.TestCase):
    """Selection rules of the leave-one-out criterion; the refits themselves are in kinetics_loo_comparison_test."""

    def best_methods(self, *models):
        return [{"model_id": model_id, "best": model.get_best_method(), "model": model} for model, model_id in models]

    def test_should_return_one_cross_validation_error_per_model(self):
        best_methods = self.best_methods(
            fitted_model(3, *pfo_predictions(), loo_rmse=0.2),
            fitted_model(2, *pso_predictions(), loo_rmse=0.4),
        )

        result = get_kinetic_ml_comparison(best_methods, sample())

        self.assertEqual(result["criterion"], "loo_cv")
        self.assertEqual(result["results"], [{"model": 3, "cv_rmse": 0.2}, {"model": 2, "cv_rmse": 0.4}])

    def test_should_pick_the_model_with_the_lowest_cross_validation_error(self):
        # The winner goes second on purpose, so "lowest error" is not confused with "first in the list".
        best_methods = self.best_methods(
            fitted_model(2, *pso_predictions(), loo_rmse=0.4),
            fitted_model(3, *pfo_predictions(), loo_rmse=0.2),
        )

        result = get_kinetic_ml_comparison(best_methods, sample())

        self.assertEqual(result["best_model"], 3)

    def test_should_leave_out_a_model_that_cannot_be_cross_validated(self):
        best_methods = self.best_methods(
            fitted_model(3, *pfo_predictions(), loo_rmse=None),
            fitted_model(2, *pso_predictions(), loo_rmse=0.4),
        )

        result = get_kinetic_ml_comparison(best_methods, sample())

        self.assertEqual([r["model"] for r in result["results"]], [2])
        self.assertEqual(result["best_model"], 2)

    def test_should_return_no_ml_block_when_no_model_can_be_cross_validated(self):
        best_methods = self.best_methods(fitted_model(3, *pfo_predictions(), loo_rmse=None))

        self.assertIsNone(get_kinetic_ml_comparison(best_methods, sample()))

    def test_should_work_with_a_single_fitted_model(self):
        best_methods = self.best_methods(fitted_model(2, *pso_predictions()))

        result = get_kinetic_ml_comparison(best_methods, sample())

        self.assertEqual(result["best_model"], 2)
        self.assertEqual(len(result["results"]), 1)


if __name__ == "__main__":
    unittest.main()
