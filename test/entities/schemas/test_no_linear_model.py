import unittest
from unittest.mock import MagicMock, patch
import numpy as np

from entities.no_linear_model import NoLinearModel
from entities.sample import SampleEntity


class TestNoLinearModel(unittest.TestCase):

    def setUp(self):
        self.ce_data = [1, 2, 3, 4, 5]
        self.qe_data = [2.1, 4.1, 6.1, 8.1, 10.1]
        self.sample = SampleEntity(ce=self.ce_data, qe=self.qe_data)
        self.initial_seeds = {'k': 0.5, 'qmax': 1.0}
        self.model = NoLinearModel(
            _id=1,
            name="Test Model",
            formula='qe = qmax * k * ce / (1 + (k * ce))',
            description="A test description",
            parameters=["k", "qmax"]
        )
        self.model.get_seeds = MagicMock(return_value=self.initial_seeds)

    def test_success(self):
        return_value = {'description': 'Levenberg-Marquardt (Gauss-Newton modificado)', 'name': 'leastsq',
             'params': {'k': 0.005485715825843923, 'qmax': 377.83653152467105},
             'stats': {'CV_RMSE': 0.33844832285616966, 'Chi_squared': 0.0008100226724587764,
                       'Chi_squared_reduced': 0.00027000755748625877, 'HYBRID': 0.026562805646959273,
                       'R2': 0.9999467212023231, 'R2_adjusted': 0.9998934424046462, 'RMSE': 0.020645347694226348,
                       'SSE': 0.002131151907077486, 'Std_error': 0.02665302926546678, 'n_params': 2, 'n_points': 5},
             'success': True, 'x': [1, 2, 3, 4, 5],
             'y_pred': [2.0613956100455124, 4.100420201153573, 6.117435975664721, 8.112797358814994,
                        10.086851206356117]}


        results = self.model.run(self.sample, self.initial_seeds)

        self.assertEqual(results[0]["y_pred"][0], return_value["y_pred"][0])
        self.assertEqual(len(results), 3)
        self.assertTrue(results[0]['success'])
        self.assertEqual(results[0]['params'], return_value["params"])

    def test_run_empty_sample(self):
        empty_sample = SampleEntity(ce=[], qe=[])
        self.model.get_seeds = MagicMock(return_value=self.initial_seeds)

        results = self.model.run(empty_sample, self.initial_seeds)

        self.assertEqual(len(results), 0)


if __name__ == '__main__':
    unittest.main()
