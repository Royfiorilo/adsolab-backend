import unittest

import numpy as np
from scipy.stats import linregress

from entities.sample import SampleEntity

from entities.linearization import Linearization


class LinearizationTest(unittest.TestCase):
    def setUp(self):
        return

    @staticmethod
    def generate_freundlich_data(kf=0.5, nf=2, num_points=10, noise_level=0.05):
        # Generar valores de ce espaciados logarítmicamente
        ce = np.logspace(-1, 2, num_points)
        qe = kf * ce ** (1 / nf)

        # Añadir un poco de ruido aleatorio
        qe *= (1 + noise_level * (np.random.random(num_points) - 0.5))

        return ce, qe

    @staticmethod
    def generate_langmuir_data(qmax=10, k=0.5, num_points=10, noise_level=0.05):
        # Generar valores de ce espaciados logarítmicamente
        ce = np.logspace(-1, 2, num_points)
        qe = (qmax * k * ce) / (1 + k * ce)

        # Añadir un poco de ruido aleatorio
        qe *= (1 + noise_level * (np.random.random(num_points) - 0.5))

        return ce, qe

    def test_linearization_HaneseWoolf(self):
        ce, qe = self.generate_langmuir_data()

        inv_ce = ce
        inv_qe = ce / qe

        slope, intercept, r_value, p_value, std_err = linregress(inv_ce, inv_qe)

        q_max = 1 / slope
        k = 1 / (intercept * q_max)

        params = (
            'HaneseWoolf Linearization', 'ce/qe = (1/qmax) * ce + 1 / (qmax * k)',
            'Linealizacion del modelo de Langmuir',
            {"x": "ce", "y": "ce/qe", "m": "1/qmax", "b": "1/(qmax * k)"}, 1)

        linearization = Linearization(1, params[0], params[1], params[2], params[3], params[4])

        sample = SampleEntity(ce, qe)
        result = linearization.run(sample)
        self.assertAlmostEqual(result['parameters'][1]['value'], q_max, places=10)
        self.assertAlmostEqual(result['parameters'][0]['value'], k, places=4)

    def test_linearization_Lineweaver_Burk(self):
        ce, qe = self.generate_langmuir_data()

        inv_ce = 1 / ce
        inv_qe = 1 / qe

        slope, intercept, r_value, p_value, std_err = linregress(inv_ce, inv_qe)

        q_max = 1 / intercept
        k = 1 / (slope * q_max)

        params = ('Lineweaver-Burk Linearization', '1 / qe = (1 / k * qmax) * (1 / ce) + 1 / qmax',
                  'Linealizacion del modelo de Langmuir', {"x": "1/ce", "y": "1/qe", "m": "1/(k*qmax)", "b": "1/qmax"},
                  1)

        linearization = Linearization(1, params[0], params[1], params[2], params[3], params[4])

        sample = SampleEntity(ce, qe)
        result = linearization.run(sample)
        self.assertAlmostEqual(result['parameters'][1]['value'], q_max, places=10)
        self.assertAlmostEqual(result['parameters'][0]['value'], k, places=4)

    def test_linearization_freundlich(self):
        ce, qe = self.generate_freundlich_data()

        inv_ce = np.log10(ce)
        inv_qe = np.log10(qe)

        slope, intercept, r_value, p_value, std_err = linregress(inv_ce, inv_qe)

        nf = 1 / slope
        kf = 10 ** intercept

        params = (
            'Freundlich linearization', 'log(qe) = log(kf) + 1/nf * log(ce)', 'Linealizacion del modelo de Freundlich',
            {"x": "log(ce)", "y": "log(qe)", "m": "1 / nf", "b": "log(kf)"}, 2)

        linearization = Linearization(1, params[0], params[1], params[2], params[3], params[4])

        sample = SampleEntity(ce, qe)
        result = linearization.run(sample)
        self.assertAlmostEqual(result['parameters'][1]['value'], nf, places=10)
        self.assertAlmostEqual(result['parameters'][0]['value'], kf, places=4)


if __name__ == '__main__':
    unittest.main()
