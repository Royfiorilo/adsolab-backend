import unittest

from entities.kinetics_sample import R_CONSTANT, KineticsSampleEntity


class TestKineticsSampleEntity(unittest.TestCase):
    def setUp(self):
        self.entity = KineticsSampleEntity(
            time=[0.0, 5.0, 10.0, 20.0, 30.0],
            qt=[0.0, 3.2, 5.1, 6.8, 7.4],
            kinetic_sample_id=7,
            title="Test Kinetic Sample",
            description="test",
            temperature=298,
            time_unit="min",
            measure_unit="mg/g",
            adsorbate_id=1,
            adsorbent_id=1,
        )

    def test_should_expose_kinetic_sample_id_as_id(self):
        self.assertEqual(self.entity.id, 7)

    def test_should_return_number_of_time_points_when_len(self):
        self.assertEqual(self.entity.len(), 5)

    def test_should_remove_single_index_from_time_and_qt(self):
        self.entity.remove([1])
        self.assertEqual(self.entity.time, [0.0, 10.0, 20.0, 30.0])
        self.assertEqual(self.entity.qt, [0.0, 5.1, 6.8, 7.4])

    def test_should_remove_multiple_indexes_from_time_and_qt(self):
        self.entity.remove([0, 2])
        self.assertEqual(self.entity.time, [5.0, 20.0, 30.0])
        self.assertEqual(self.entity.qt, [3.2, 6.8, 7.4])

    def test_should_keep_sample_untouched_when_removing_empty_list(self):
        self.entity.remove([])
        self.assertEqual(self.entity.time, [0.0, 5.0, 10.0, 20.0, 30.0])
        self.assertEqual(self.entity.qt, [0.0, 3.2, 5.1, 6.8, 7.4])

    def test_should_also_remove_concentration_when_present(self):
        self.entity.concentration = [50.0, 40.0, 33.0, 27.0, 24.0]
        self.entity.remove([1, 3])
        self.assertEqual(self.entity.time, [0.0, 10.0, 30.0])
        self.assertEqual(self.entity.qt, [0.0, 5.1, 7.4])
        self.assertEqual(self.entity.concentration, [50.0, 33.0, 24.0])

    def test_should_return_temperature_and_gas_constant_as_constants(self):
        self.assertEqual(self.entity.constants, {"T": 298, "R": R_CONSTANT})

    def test_should_build_sample_name_with_username_temperature_and_materials(self):
        name = self.entity.create_sample_name("francisco", "Cd", "carbon")
        self.assertTrue(name.startswith("francisco-298K-cinetica-Cd-carbon-"))

    def test_should_use_placeholder_temperature_when_missing(self):
        self.entity.temperature = None
        name = self.entity.create_sample_name("francisco", "Cd", "carbon")
        self.assertTrue(name.startswith("francisco-?K-cinetica-Cd-carbon-"))


if __name__ == "__main__":
    unittest.main()
