import math
import unittest
from unittest.mock import patch

from entities.kinetics_sample import KineticsSampleEntity
from services.kinetics_no_linear_model_service import (
    KineticNoLinearModel,
    calculate_kinetic_seeds,
    run_kinetic_no_linear_models,
)

QE, K1, K2, KID, C = 7.5, 0.15, 0.02, 1.2, 0.5
FIT_TIMES = [0.0, 5.0, 10.0, 20.0, 30.0, 45.0, 60.0]

PFO_MODEL = {"_id": 3, "name": "PFO", "formula": "qt = qe * (1 - exp(-k1 * time))",
             "parameters": {"qe": "", "k1": ""}}
PSO_MODEL = {"_id": 2, "name": "PSO", "formula": "qt = (k2 * qe**2 * time) / (1 + k2 * qe * time)",
             "parameters": {"qe": "", "k2": ""}}

EXPECTED_STATISTICS = ["r_squared", "adjust_r_squared", "chi_squared", "adjust_chi_squeared",
                       "RMSE", "SSE", "HYBRID", "AIC", "BIC"]
EXPECTED_RESIDUAL_ANALYSIS = ["normality_pvalue", "homoscedasticity_pvalue", "durbin_watson",
                              "passes_normality", "passes_homoscedasticity", "passes_independence"]


def seeds_by_name(seeds):
    return {seed["name"]: seed["value"] for seed in seeds}


def pfo_sample():
    return KineticsSampleEntity(
        time=list(FIT_TIMES), qt=[QE * (1 - math.exp(-K1 * t)) for t in FIT_TIMES]
    )


def run_fit(model_data, sample, seeds):
    model = KineticNoLinearModel(model_data)
    model.run(sample=sample, seeds=seeds, methods={"leastsq": "Least Squares"}, iterations=2000)
    return model.get_best_method()


class TestCalculateKineticSeeds(unittest.TestCase):
    def setUp(self):
        self.sample = KineticsSampleEntity(
            time=[0.0, 5.0, 10.0, 20.0, 30.0],
            qt=[0.0, 3.2, 5.1, 6.8, 7.4],
        )

    def test_should_seed_pseudo_first_order_with_max_qt_and_default_k1(self):
        seeds = calculate_kinetic_seeds(
            self.sample, {"parameters": {"qe": {}, "k1": {}}}
        )

        self.assertEqual(seeds_by_name(seeds), {"qe": 7.4, "k1": 0.1})

    def test_should_seed_pseudo_second_order_with_max_qt_and_default_k2(self):
        seeds = calculate_kinetic_seeds(
            self.sample, {"parameters": {"qe": {}, "k2": {}}}
        )

        self.assertEqual(seeds_by_name(seeds), {"qe": 7.4, "k2": 0.01})

    def test_should_seed_intraparticle_diffusion_from_max_qt_over_sqrt_max_time(self):
        seeds = seeds_by_name(
            calculate_kinetic_seeds(self.sample, {"parameters": {"kid": {}, "C": {}}})
        )

        self.assertAlmostEqual(seeds["kid"], 7.4 / (30.0 ** 0.5), places=6)
        self.assertEqual(seeds["C"], 1.0)

    def test_should_seed_unknown_parameter_with_one(self):
        seeds = calculate_kinetic_seeds(self.sample, {"parameters": {"alpha": {}}})

        self.assertEqual(seeds_by_name(seeds), {"alpha": 1.0})

    def test_should_return_empty_seeds_when_model_has_no_parameters(self):
        self.assertEqual(calculate_kinetic_seeds(self.sample, {}), [])

    def test_should_fall_back_to_one_when_sample_has_no_points(self):
        empty_sample = KineticsSampleEntity(time=[], qt=[])

        seeds = calculate_kinetic_seeds(
            empty_sample, {"parameters": {"qe": {}, "kid": {}}}
        )

        self.assertEqual(seeds_by_name(seeds), {"qe": 1.0, "kid": 1.0})


class TestFitStatisticsAndResiduals(unittest.TestCase):
    def setUp(self):
        self.sample = pfo_sample()
        self.best = run_fit(PFO_MODEL, self.sample,
                            [{"name": "qe", "value": 7.0}, {"name": "k1", "value": 0.1}])

    def test_should_recover_the_known_parameters(self):
        params = {p["name"]: p["value"] for p in self.best.parameters}

        self.assertAlmostEqual(params["qe"], QE, places=3)
        self.assertAlmostEqual(params["k1"], K1, places=3)

    def test_should_produce_every_statistic(self):
        for name in EXPECTED_STATISTICS:
            self.assertIn(name, self.best.statistics)
            self.assertIsNotNone(self.best.statistics[name], name)

    def test_should_produce_one_residual_per_experimental_point(self):
        self.assertEqual(len(self.best.residuals["values"]), len(FIT_TIMES))

    def test_should_produce_the_full_residual_analysis(self):
        for name in EXPECTED_RESIDUAL_ANALYSIS:
            self.assertIn(name, self.best.residuals["analysis"])

    def test_should_keep_qt_pred_in_transformed_for_the_ridge_comparison(self):
        self.assertIn("qt_pred", self.best.transformed)
        self.assertEqual(len(self.best.transformed["qt_pred"]), len(FIT_TIMES))

    def test_should_extend_the_curve_beyond_the_experimental_points(self):
        self.assertGreater(len(self.best.transformed["x"]), len(FIT_TIMES))
        self.assertEqual(len(self.best.transformed["x"]), len(self.best.transformed["y"]))

    def test_should_use_the_same_extended_grid_for_every_model_of_a_sample(self):
        other = run_fit(PSO_MODEL, self.sample,
                        [{"name": "qe", "value": 7.0}, {"name": "k2", "value": 0.01}])

        self.assertEqual(list(self.best.transformed["x"]), list(other.transformed["x"]))


class TestRunKineticNoLinearModels(unittest.TestCase):
    def run_service(self, seeds):
        request = {
            "kinetic_sample_id": 1,
            "filter": [],
            "models": [{"model": PFO_MODEL["_id"], "seeds": seeds, "iterations": 2000}],
        }
        with patch('services.kinetics_sample_service.find_kinetic_sample', return_value=pfo_sample()), \
                patch('services.kinetics_no_linear_model_service.find_kinetic_model', return_value=PFO_MODEL), \
                patch('services.kinetics_no_linear_model_service.get_optimization_methods',
                      return_value={"leastsq": "Least Squares"}):
            return run_kinetic_no_linear_models(request)

    def test_should_echo_the_seeds_of_every_model(self):
        seeds = [{"name": "qe", "value": 7.0}, {"name": "k1", "value": 0.1}]

        results, _ = self.run_service(seeds)

        self.assertEqual(results[0]["seeds"], seeds)

    def test_should_return_statistics_and_residuals_per_adjustment_method(self):
        results, _ = self.run_service([{"name": "qe", "value": 7.0}, {"name": "k1", "value": 0.1}])
        method = results[0]["adjustment_methods"][0]

        for name in EXPECTED_STATISTICS:
            self.assertIn(name, method["statistics"])
        for name in EXPECTED_RESIDUAL_ANALYSIS:
            self.assertIn(name, method["residuals"]["analysis"])

    def test_should_return_a_comparison_with_heuristic_and_ml_blocks(self):
        _, comparison = self.run_service([{"name": "qe", "value": 7.0}, {"name": "k1", "value": 0.1}])

        self.assertIsNotNone(comparison["heuristic"])
        self.assertIsNotNone(comparison["ml"])
        self.assertEqual(comparison["ml"]["best_model"], PFO_MODEL["_id"])


if __name__ == "__main__":
    unittest.main()
