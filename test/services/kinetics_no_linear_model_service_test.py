import unittest

from entities.kinetics_sample import KineticsSampleEntity
from services.kinetics_no_linear_model_service import calculate_kinetic_seeds


def seeds_by_name(seeds):
    return {seed["name"]: seed["value"] for seed in seeds}


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


if __name__ == "__main__":
    unittest.main()
