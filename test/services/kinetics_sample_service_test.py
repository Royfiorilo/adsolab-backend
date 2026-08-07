import unittest

from entities.kinetics_sample import KineticsSampleEntity
from exceptions.exceptions import FilterSampleError
from services.kinetics_sample_service import (
    calculate_qt_from_concentration,
    filter_kinetic_sample,
    order_sample,
)


class TestOrderSample(unittest.TestCase):
    def test_should_sort_pairs_by_time_when_data_is_unordered(self):
        time, qt = order_sample([30, 0, 10, 5, 20], [7.4, 0.0, 5.1, 3.2, 6.8])

        self.assertEqual(time, [0, 5, 10, 20, 30])
        self.assertEqual(qt, [0.0, 3.2, 5.1, 6.8, 7.4])

    def test_should_keep_order_when_data_is_already_sorted(self):
        time, qt = order_sample([0, 5, 10], [0.0, 3.2, 5.1])

        self.assertEqual(time, [0, 5, 10])
        self.assertEqual(qt, [0.0, 3.2, 5.1])


class TestCalculateQtFromConcentration(unittest.TestCase):
    def test_should_apply_mass_balance_formula(self):
        qt = calculate_qt_from_concentration(
            concentration=[50.0, 40.0, 30.0],
            initial_concentration=50.0,
            volume=0.25,
            adsorbent_mass=0.5,
        )

        self.assertEqual(qt, [0.0, 5.0, 10.0])

    def test_should_return_empty_list_when_no_concentration_points(self):
        qt = calculate_qt_from_concentration(
            concentration=[],
            initial_concentration=50.0,
            volume=0.25,
            adsorbent_mass=0.5,
        )

        self.assertEqual(qt, [])


class TestFilterKineticSample(unittest.TestCase):
    def setUp(self):
        self.sample = KineticsSampleEntity(
            time=[0.0, 5.0, 10.0, 20.0, 30.0],
            qt=[0.0, 3.2, 5.1, 6.8, 7.4],
        )

    def test_should_return_sample_untouched_when_no_indexes(self):
        result = filter_kinetic_sample(self.sample, [])

        self.assertEqual(result.time, [0.0, 5.0, 10.0, 20.0, 30.0])
        self.assertEqual(result.qt, [0.0, 3.2, 5.1, 6.8, 7.4])

    def test_should_remove_requested_indexes(self):
        result = filter_kinetic_sample(self.sample, [1, 3])

        self.assertEqual(result.time, [0.0, 10.0, 30.0])
        self.assertEqual(result.qt, [0.0, 5.1, 7.4])

    def test_should_raise_when_index_is_out_of_range(self):
        with self.assertRaises(FilterSampleError):
            filter_kinetic_sample(self.sample, [10])

    def test_should_raise_when_index_is_negative(self):
        with self.assertRaises(FilterSampleError):
            filter_kinetic_sample(self.sample, [-1])

    def test_should_raise_when_more_indexes_than_points(self):
        with self.assertRaises(FilterSampleError):
            filter_kinetic_sample(self.sample, [0, 1, 2, 3, 4, 5])


if __name__ == "__main__":
    unittest.main()
