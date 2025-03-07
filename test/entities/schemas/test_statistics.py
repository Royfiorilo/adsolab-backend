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
        """Test linear_r_squeared calculation"""
        pearson_coef = 0.95
        expected_r2 = 0.9025  # 0.95^2
        result = Statistics.linear_r_squeared(pearson_coef)
        self.assertAlmostEqual(result, expected_r2)

    def test_adjust_r_squared(self):
        """Test adjust_r_squared calculation"""
        with patch.object(Statistics, 'r_squared', return_value=0.95) as mock_r2:
            result = Statistics.adjust_r_squared(self.y_exp, self.y_pred, self.num_params)
            mock_r2.assert_called_once_with(self.y_exp, self.y_pred)
            # Expected calculation: 1 - (((5-1)/(5-2-1)) * (1-0.95))
            # = 1 - ((4/2) * 0.05) = 1 - 0.1 = 0.9
            self.assertAlmostEqual(result, 0.9)

    def test_chi_squared(self):
        """Test chi_squared calculation"""
        # Create a simple case where the calculation is predictable
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
        """Test adjust_chi_squared calculation"""
        with patch.object(Statistics, 'chi_squared', return_value=10.0) as mock_chi2:
            result = Statistics.adjust_chi_squared(self.y_exp, self.y_pred, self.num_params)
            mock_chi2.assert_called_once_with(self.y_exp, self.y_pred)
            # Expected: 10.0 / (5 - 2) = 10/3 = 3.333...
            self.assertAlmostEqual(result, 10.0 / (len(self.y_exp) - self.num_params))

    def test_rmse(self):
        """Test rmse calculation"""
        with patch('sklearn.metrics.mean_squared_error', return_value=0.04) as mock_mse:
            result = Statistics.rmse(self.y_exp, self.y_pred)
            mock_mse.assert_called_once_with(self.y_exp, self.y_pred)
            # Expected: sqrt(0.04) = 0.2
            self.assertAlmostEqual(result, 0.2)

    def test_sse(self):
        """Test sse calculation"""
        # Expected: sum((y_exp - y_pred)^2)
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

    def test_all_statistics(self):
        """Test all_statistics calculation"""
        # Mock all the individual statistic methods
        with patch.object(Statistics, 'r_squared', return_value=0.95) as mock_r2, \
                patch.object(Statistics, 'adjust_r_squared', return_value=0.93) as mock_adj_r2, \
                patch.object(Statistics, 'chi_squared', return_value=1.5) as mock_chi2, \
                patch.object(Statistics, 'adjust_chi_squared', return_value=0.75) as mock_adj_chi2, \
                patch.object(Statistics, 'rmse', return_value=0.2) as mock_rmse, \
                patch.object(Statistics, 'sse', return_value=0.5) as mock_sse, \
                patch.object(Statistics, 'hybrid', return_value=1.2) as mock_hybrid, \
                patch('utils.round_number', side_effect=lambda x: round(x, 4) if x is not None else None) as mock_round:
            result = Statistics.all_statistics(self.y_exp, self.y_pred, self.num_params, self.aic, self.bic)

            # Check that all methods were called correctly
            mock_r2.assert_called_once_with(self.y_exp, self.y_pred)
            mock_adj_r2.assert_called_once_with(self.y_exp, self.y_pred, self.num_params)
            mock_chi2.assert_called_once_with(self.y_exp, self.y_pred)
            mock_adj_chi2.assert_called_once_with(self.y_exp, self.y_pred, self.num_params)
            mock_rmse.assert_called_once_with(self.y_exp, self.y_pred)
            mock_sse.assert_called_once_with(self.y_exp, self.y_pred)
            mock_hybrid.assert_called_once_with(self.y_exp, self.y_pred, self.num_params)

            # Check that the function returns the expected dictionary
            expected_dict = {
                "r_squared": 0.95,
                "adjust_r_squared": 0.93,
                "chi_squared": 1.5,
                "adjust_chi_squeared": 0.75,
                "RMSE": 0.2,
                "SSE": 0.5,
                "HYBRID": 1.2,
                "AIC": 10.5,
                "BIC": 12.3
            }
            self.assertEqual(result, expected_dict)

            # Test with hybrid = None
            mock_hybrid.return_value = None
            result_none_hybrid = Statistics.all_statistics(self.y_exp, self.y_pred, self.num_params, self.aic, self.bic)
            expected_dict["HYBRID"] = None
            self.assertEqual(result_none_hybrid, expected_dict)

    def test_check_residuals(self):
        """Test check_residuals calculation"""
        # Mock the scipy.stats functions and durbin_watson
        with patch('scipy.stats.shapiro', return_value=(0.8, 0.06)) as mock_shapiro, \
                patch('scipy.stats.levene', return_value=(0.7, 0.04)) as mock_levene, \
                patch('statsmodels.stats.stattools.durbin_watson', return_value=2.2) as mock_dw, \
                patch('utils.round_number', side_effect=lambda x: round(x, 4)) as mock_round:
            result = Statistics.check_residuals(self, self.residuals)

            # Check function calls
            mock_shapiro.assert_called_once_with(self.residuals)
            mock_levene.assert_called_once_with(self.residuals, np.ones_like(self.residuals))
            mock_dw.assert_called_once_with(self.residuals)

            # Expected values based on mock returns
            expected_dict = {
                'normality_pvalue': 0.06,  # > 0.05, so passes
                'homoscedasticity_pvalue': 0.04,  # < 0.05, so fails
                'durbin_watson': 2.2,  # Between 1.5 and 2.5, so fails
                'passes_normality': 0,  # 0 means passes (p > 0.05)
                'passes_homoscedasticity': 1,  # 1 means fails (p <= 0.05)
                'passes_independence': 0,  # 0 means fails (1.5 < dw < 2.5)
            }
            self.assertEqual(result, expected_dict)

            # Test with different values to trigger different branches
            mock_shapiro.return_value = (0.8, 0.03)  # p < 0.05, fails normality
            mock_levene.return_value = (0.7, 0.06)  # p > 0.05, passes homoscedasticity
            mock_dw.return_value = 3.0  # > 2.5, passes independence (no autocorrelation)

            result2 = Statistics.check_residuals(self, self.residuals)

            expected_dict2 = {
                'normality_pvalue': 0.03,
                'homoscedasticity_pvalue': 0.06,
                'durbin_watson': 3.0,
                'passes_normality': 1,  # 1 means fails (p <= 0.05)
                'passes_homoscedasticity': 0,  # 0 means passes (p > 0.05)
                'passes_independence': 1,  # 1 means passes (dw outside [1.5, 2.5])
            }
            self.assertEqual(result2, expected_dict2)

    def test_get_outliers(self):
        """Test get_outliers function"""
        # Create mock for pd.concat
        concat_result = pd.DataFrame({'residuals': [-0.1, 0.1, 0.2, 0.3, 5.0, -4.0]})

        with patch('pandas.concat', return_value=concat_result) as mock_concat:
            result = Statistics.get_outliers(self, self.residuals_list)

            # Verify concat was called correctly
            mock_concat.assert_called_once()
            args, kwargs = mock_concat.call_args
            self.assertEqual(args[0], self.residuals_list)
            self.assertEqual(kwargs, {'ignore_index': True})

            # Values outside [Q1-1.5*IQR, Q3+1.5*IQR] are outliers
            # Q1 = -0.05, Q3 = 0.3, IQR = 0.35
            # Lower bound = -0.05 - 1.5*0.35 = -0.575
            # Upper bound = 0.3 + 1.5*0.35 = 0.825
            # Values 5.0 and -4.0 are outliers

            # The function should return a list of outliers, check if it contains 5.0 and -4.0
            self.assertIn(5.0, [x['residuals'] for x in result])
            self.assertIn(-4.0, [x['residuals'] for x in result])
            self.assertEqual(len(result), 2)  # There should be 2 outliers


if __name__ == '__main__':
    unittest.main()