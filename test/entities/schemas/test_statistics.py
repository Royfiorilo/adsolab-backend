import unittest
import numpy as np
import pandas as pd
from unittest.mock import patch
from entities.statistics import Statistics


class TestStatistics(unittest.TestCase):
    def setUp(self):
        self.y_exp = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        self.y_pred = np.array([1.1, 2.2, 2.8, 3.9, 5.2])
        self.num_params = 2
        self.aic = 10.5
        self.bic = 12.3
        self.residuals = np.array([0.1, 0.2, -0.2, -0.1, 0.2])
        self.residuals_list = [
            pd.DataFrame({'residuals': [-0.1, 0.1, 0.2]}),
            pd.DataFrame({'residuals': [0.3, 5.0, -4.0]})
        ]

    def test_singleton_pattern(self):
        """Test that Statistics class implements singleton pattern correctly"""
        instance1 = Statistics()
        instance2 = Statistics()
        self.assertIs(instance1, instance2)

    def test_r_squared(self):
        result = Statistics.r_squared(self.y_exp, self.y_pred)
        self.assertEqual(result, 0.986)

    def test_linear_r_squeared(self):
        pearson_coef = 0.95
        expected_r2 = 0.9025  # 0.95^2
        result = Statistics.linear_r_squeared(pearson_coef)
        self.assertAlmostEqual(result, expected_r2)

    def test_adjust_r_squared(self):
        result = Statistics.adjust_r_squared(self.y_exp, self.y_pred, self.num_params)
        self.assertAlmostEqual(result,0.972, places=3)

    def test_chi_squared(self):
        y_exp = np.array([10, 20, 30, 40])
        y_pred = np.array([9, 21, 31, 39])

        result = Statistics.chi_squared(y_exp, y_pred)

        # The function normalizes the arrays, so we need to calculate the expected result
        # with normalized values
        y_exp_norm = y_exp / np.sum(y_exp)
        y_pred_norm = y_pred / np.sum(y_pred)
        expected = np.sum(((y_pred_norm - y_exp_norm) ** 2) / np.abs(y_exp_norm))

        self.assertAlmostEqual(result, expected)

    def test_adjust_chi_squared(self):
        expected = Statistics.chi_squared(self.y_exp, self.y_pred) / (len(self.y_exp) - self.num_params)
        result = Statistics.adjust_chi_squared(self.y_exp, self.y_pred, self.num_params)
        self.assertAlmostEqual(result, expected)

    def test_rmse(self):
        result = Statistics.rmse(self.y_exp, self.y_pred)
        self.assertAlmostEqual(result, 0.167, places=3)

    def test_sse(self):
        expected = np.sum((self.y_exp - self.y_pred) ** 2)
        result = Statistics.sse(self.y_exp, self.y_pred)
        self.assertAlmostEqual(result, expected)

    def test_hybrid(self):
        """Test hybrid calculation"""
        # Test with valid data
        y_exp = np.array([10.0, 20.0, 30.0])
        y_pred = np.array([11.0, 19.0, 31.0])
        num_params = 1

        # Expected: (100 / (3 - 1)) * sum((y_exp - y_pred)^2 / y_exp)
        diff = y_exp - y_pred
        expected = (100 / (len(y_exp) - num_params)) * np.sum((diff ** 2) / y_exp)

        result = Statistics.hybrid(y_exp, y_pred, num_params)
        self.assertAlmostEqual(result, expected)

        # Test with n <= 1 (should return None)
        y_exp_small = np.array([10.0])
        y_pred_small = np.array([11.0])
        result_small = Statistics.hybrid(y_exp_small, y_pred_small, num_params)
        self.assertIsNone(result_small)

        # Test with zero values in y_exp (should filter them out)
        y_exp_with_zero = np.array([0.0, 20.0, 30.0])
        y_pred_with_zero = np.array([11.0, 19.0, 31.0])
        # Only the last two elements should be used in calculation
        diff_filtered = y_exp_with_zero[1:] - y_pred_with_zero[1:]
        expected_filtered = (100 / (2 - num_params)) * np.sum((diff_filtered ** 2) / y_exp_with_zero[1:])

        result_with_zero = Statistics.hybrid(y_exp_with_zero, y_pred_with_zero, num_params)
        self.assertAlmostEqual(result_with_zero, expected_filtered)


    def test_get_outliers(self):
        outliers = Statistics.get_outliers(self.residuals_list)
        expected_outliers = [5.0, -4.0]
        self.assertEqual(sorted(outliers), sorted(expected_outliers))
        self.assertIsInstance(outliers, list)

    def test_check_residuals_format(self):
        result = Statistics.check_residuals(self.residuals)

        self.assertIn('normality_pvalue', result)
        self.assertIn('homoscedasticity_pvalue', result)
        self.assertIn('durbin_watson', result)
        self.assertIn('passes_normality', result)
        self.assertIn('passes_homoscedasticity', result)
        self.assertIn('passes_independence', result)

        self.assertIsInstance(result['normality_pvalue'], float)
        self.assertIsInstance(result['homoscedasticity_pvalue'], float)
        self.assertIsInstance(result['durbin_watson'], float)
        self.assertIsInstance(result['passes_normality'], int)
        self.assertIsInstance(result['passes_homoscedasticity'], int)
        self.assertIsInstance(result['passes_independence'], int)

        self.assertGreaterEqual(result['normality_pvalue'], 0.0)
        self.assertLessEqual(result['normality_pvalue'], 1.0)
        self.assertGreaterEqual(result['homoscedasticity_pvalue'], 0.0)
        self.assertLessEqual(result['homoscedasticity_pvalue'], 1.0)
        self.assertGreaterEqual(result['durbin_watson'], 0.0)
        self.assertLessEqual(result['durbin_watson'], 4.0)

    @patch('entities.statistics.durbin_watson', return_value=2.12345)
    @patch('scipy.stats.levene', return_value=(0, 0.67890))
    @patch('scipy.stats.shapiro', return_value=(0, 0.12345))
    def test_check_residuals_rounding(self, mock_shapiro, mock_levene, mock_durbin_watson):
        # Mock statistical test results to have more decimal places
        result = Statistics.check_residuals(self.residuals)

        # Check that values are rounded to 3 decimal places
        self.assertAlmostEqual(result['normality_pvalue'], 0.1235, places=3)
        self.assertAlmostEqual(result['homoscedasticity_pvalue'], 0.679, places=3)
        self.assertAlmostEqual(result['durbin_watson'], 2.123, places=3)


if __name__ == '__main__':
    unittest.main()