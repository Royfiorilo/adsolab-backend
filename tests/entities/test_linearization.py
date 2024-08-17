import unittest

import numpy as np
from scipy.stats import linregress

from entities.sample import SampleEntity
from entities.linearization import Linearization


class LinearizationTest(unittest.TestCase):
    def setUp(self):
        return

    def generate_langmuir_data(self,qmax=10, k=0.5, num_points=10, noise_level=0.05):
        # Generar valores de ce espaciados logarítmicamente
        ce = np.logspace(-1, 2, num_points)
        qe = (qmax * k * ce) / (1 + k * ce)

        # Añadir un poco de ruido aleatorio
        qe *= (1 + noise_level * (np.random.random(num_points) - 0.5))

        return ce, qe

    def test_linearization_(self):
        ce, qe = self.generate_langmuir_data()

        inv_ce = 1 / ce
        inv_qe = 1 / qe

        slope, intercept, r_value, p_value, std_err = linregress(inv_ce, inv_qe)

        q_max = 1 / intercept
        k = 1 / (slope * q_max)


        params = ('HaneseWoolf Linearization', 'ce/qe = (1/qmax) * ce + 1 / (qmax * k)', 'Linealizacion del modelo de Langmuir', {"x": "ce", "y": "ce/qe"}, 1)

        linearization = Linearization(1,params[0], params[1], params[2], params[3], params[4])

        sample = SampleEntity(ce, qe)
        result = linearization.run(sample)

        assert result["q_max"] == q_max
        assert result["k"] == k


if __name__ == '__main__':
    unittest.main()
