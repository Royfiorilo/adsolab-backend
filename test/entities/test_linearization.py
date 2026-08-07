import unittest
from app.utils import round_list_numbers

import numpy as np

from entities.sample import SampleEntity

from entities.linearization import Linearization

ROUND_DIGIT = 4
R_CONSTANT = 8.3144598

class LinearizationTest(unittest.TestCase):
    def setUp(self):
        self.sample = SampleEntity(
            ce=[0, 0.0067763, 0.015759, 0.0316021, 0.041034, 0.1198222, 0.1371802, 0.289058, 0.36124, 0.420855],
            qe=[0, 0.0259714, 0.035572, 0.0428751, 0.068788, 0.0732422, 0.092398, 0.14434, 0.1301768, 0.161924],
            sample_id= 1,
            temperature=290,
            measure_unit="mmol",
            adsorbate_id=1,
            adsorbent_id=3
        )
        self.sample_mock = SampleEntity(
            ce=[0, 1, 2, 3 , 4],
            qe=[0, 2, 4, 6, 8],
            sample_id= 1,
            temperature=290,
            measure_unit="mmol",
            adsorbate_id=1,
            adsorbent_id=3
        )

    def test_calculate_dots_hanesewolf(self):
        linearization = Linearization(
            linearization_id=1,
            name='HaneseWoolf Linearization',
            formula='ce/qe = (1/qmax) * ce + 1 / (qmax * k)',
            description='Test Linearization',
            parameters={"x": "ce", "y": "ce/qe", "m": "1/qmax", "b": "1/(qmax * k)"},
            latex_formula='',
            model_id=1
        )

        ce_transformed = np.array(self.sample.ce)
        qe_transformed = np.array(self.sample.ce) / np.array(self.sample.qe)
        ce_transformed = np.nan_to_num(ce_transformed, nan=0.0, posinf=0.0, neginf=0.0)
        qe_transformed = np.nan_to_num(qe_transformed, nan=0.0, posinf=0.0, neginf=0.0)


        ce_dots, qe_dots = linearization._calculate_dots(self.sample)

        assert ce_dots == round_list_numbers(ce_transformed.tolist(), ROUND_DIGIT)
        assert qe_dots == round_list_numbers(qe_transformed.tolist(), ROUND_DIGIT)

    def test_calculate_dots_lineweaver(self):
        linearization = Linearization(
            linearization_id=1,
            name='Lineweaver-Burk Linearization',
            formula='1 / qe = (1 / k * qmax) * (1 / ce) + 1 / qmax',
            description='Test Linearization',
            parameters={"x": "1/ce", "y": "1/qe", "m": "1/(k*qmax)", "b": "1/qmax"},
            latex_formula='',
            model_id=1
        )

        ce_transformed = 1 / np.array(self.sample.ce)
        qe_transformed = 1 / np.array(self.sample.qe)
        ce_transformed = np.nan_to_num(ce_transformed, nan=0.0, posinf=0.0, neginf=0.0)
        qe_transformed = np.nan_to_num(qe_transformed, nan=0.0, posinf=0.0, neginf=0.0)

        ce_dots, qe_dots = linearization._calculate_dots(self.sample)

        assert ce_dots == round_list_numbers(ce_transformed.tolist(), ROUND_DIGIT)
        assert qe_dots == round_list_numbers(qe_transformed.tolist(), ROUND_DIGIT)

    def test_calculate_dots_freundlich_linearization(self):
        linearization = Linearization(
            linearization_id=1,
            name='Freundlich Linearization',
            formula='log(qe) = log(kf) + 1/nf * log(ce)',
            description='Test Linearization',
            parameters={"x": "log(ce)", "y": "log(qe)", "m": "1 / nf", "b": "log(kf)"},
            latex_formula='',
            model_id=1
        )

        ce_transformed = np.log(np.array(self.sample.ce))
        qe_transformed = np.log(np.array(self.sample.qe))
        ce_transformed = np.nan_to_num(ce_transformed, nan=0.0, posinf=0.0, neginf=0.0)
        qe_transformed = np.nan_to_num(qe_transformed, nan=0.0, posinf=0.0, neginf=0.0)

        ce_dots, qe_dots = linearization._calculate_dots(self.sample)

        assert ce_dots == round_list_numbers(ce_transformed.tolist(), ROUND_DIGIT)
        assert qe_dots == round_list_numbers(qe_transformed.tolist(), ROUND_DIGIT)


    def test_calculate_dots_temkin_linearization(self):
        linearization = Linearization(
            linearization_id=1,
            name='Temkin Linearization',
            formula='qe = ((R*T)/btk) * ln(ktk) + ((R*T)/btk) * ln(ce)',
            description='Test Linearization',
            parameters={"x": "ln(ce)", "y": "qe", "m":"((R*T)/btk)", "b":"((R*T)/btk) * ln(ktk)"},
            latex_formula='',
            model_id=1
        )

        ce_transformed = np.log(np.array(self.sample.ce))
        qe_transformed = np.array(self.sample.qe)
        ce_transformed = np.nan_to_num(ce_transformed, nan=0.0, posinf=0.0, neginf=0.0)
        qe_transformed = np.nan_to_num(qe_transformed, nan=0.0, posinf=0.0, neginf=0.0)

        ce_dots, qe_dots = linearization._calculate_dots(self.sample)

        assert ce_dots == round_list_numbers(ce_transformed.tolist(), ROUND_DIGIT)
        assert qe_dots == round_list_numbers(qe_transformed.tolist(), ROUND_DIGIT)


    def test_linearization_HaneseWoolf(self):
        linearization = Linearization(
            linearization_id=1,
            name='HaneseWoolf Linearization',
            formula='ce/qe = (1/qmax) * ce + 1 / (qmax * k)',
            description='Test Linearization',
            parameters={"x": "ce", "y": "ce/qe", "m": "1/qmax", "b": "1/(qmax * k)"},
            latex_formula='',
            model_id=1
        )

        ce_transformed = np.array(self.sample.ce)
        qe_transformed = np.array(self.sample.ce) / np.array(self.sample.qe)
        ce_transformed = np.nan_to_num(ce_transformed, nan=0.0, posinf=0.0, neginf=0.0)
        qe_transformed = np.nan_to_num(qe_transformed, nan=0.0, posinf=0.0, neginf=0.0)

        m = 5.99
        b = 0.4

        qmax = 1/ m
        k = 1 / (b * qmax)

        result = linearization.run(self.sample, {})
        # Validamos que se calculó correctamente la pendiente y la intersección
        self.assertAlmostEqual(result["slope"], m, places=2)
        self.assertAlmostEqual(result["intercept"], b, places=2)
        self.assertAlmostEqual(result["params_info"][0]["k"], k, places=2 )
        self.assertAlmostEqual(result["params_info"][0]["qmax"], qmax, places=2)

        # Validamos que los puntos transformados sean correctos
        self.assertEqual(result["x"], round_list_numbers(ce_transformed.tolist()),ROUND_DIGIT)
        self.assertEqual(result["y"], round_list_numbers(qe_transformed.tolist()),ROUND_DIGIT)

        # Validamos el coeficiente de determinación R²
        self.assertAlmostEqual(result["statistics"]["r_squared"], 0.958, places=1)

    def test_linearization_Lineweaver_Burk(self):
        linearization = Linearization(
            linearization_id=1,
            name='Lineweaver-Burk Linearization',
            formula='1 / qe = (1 / k * qmax) * (1 / ce) + 1 / qmax',
            description='Test Linearization',
            parameters={"x": "1/ce", "y": "1/qe", "m": "1/(k*qmax)", "b": "1/qmax"},
            latex_formula='',
            model_id=1
        )

        ce_transformed = 1 / np.array(self.sample.ce)
        qe_transformed = 1 / np.array(self.sample.qe)
        ce_transformed = np.nan_to_num(ce_transformed, nan=0.0, posinf=0.0, neginf=0.0)
        qe_transformed = np.nan_to_num(qe_transformed, nan=0.0, posinf=0.0, neginf=0.0)

        m = 0.233
        b = 8.175

        qmax = 1 / b
        k = 1 / (m * qmax)

        result = linearization.run(self.sample, {})
        # Validamos que se calculó correctamente la pendiente y la intersección
        self.assertAlmostEqual(result["slope"], m, places=2)
        self.assertAlmostEqual(result["intercept"], b, places=2)
        self.assertAlmostEqual(result["params_info"][0]["qmax"], qmax, delta=0.05)
        self.assertAlmostEqual(result["params_info"][0]["k"], k, delta=0.07)

        # Validamos que los puntos transformados sean correctos
        self.assertEqual(result["x"], round_list_numbers(ce_transformed.tolist()), ROUND_DIGIT)
        self.assertEqual(result["y"], round_list_numbers(qe_transformed.tolist()), ROUND_DIGIT)

        # Validamos el coeficiente de determinación R²
        self.assertAlmostEqual(result["statistics"]["r_squared"], 0.9171, places=4)

    def test_linearization_Freundlich(self):
        linearization = Linearization(
            linearization_id=1,
            name='Freundlich Linearization',
            formula='log(qe) = log(kf) + 1/nf * log(ce)',
            description='Test Linearization',
            parameters={"x": "log(ce)", "y": "log(qe)", "m": "1 / nf", "b": "log(kf)"},
            latex_formula='',
            model_id=1
        )

        ce_transformed = np.log(np.array(self.sample.ce))
        qe_transformed = np.log(np.array(self.sample.qe))
        ce_transformed = np.nan_to_num(ce_transformed, nan=0.0, posinf=0.0, neginf=0.0)
        qe_transformed = np.nan_to_num(qe_transformed, nan=0.0, posinf=0.0, neginf=0.0)


        m = 0.585
        b = -1.013

        nf = 1 / m
        kf = np.e ** b

        result = linearization.run(self.sample, {})
        # Validamos que se calculó correctamente la pendiente y la intersección
        self.assertAlmostEqual(result["slope"], m, places=2)
        self.assertAlmostEqual(result["intercept"], b, places=2)
        self.assertAlmostEqual(result["params_info"][0]["nf"], nf, delta=0.02)
        self.assertAlmostEqual(result["params_info"][0]["kf"], kf, delta=0.02)

        # Validamos que los puntos transformados sean correctos
        self.assertEqual(result["x"], round_list_numbers(ce_transformed.tolist()), ROUND_DIGIT)
        self.assertEqual(result["y"], round_list_numbers(qe_transformed.tolist()), ROUND_DIGIT)

        # Validamos el coeficiente de determinación R²
        self.assertAlmostEqual(result["statistics"]["r_squared"], 0.91, delta=0.01)

    def test_linearization_Temkin(self):
        linearization = Linearization(
            linearization_id=1,
            name='Temkin Linearization',
            formula='qe = ((R * T)/btk) * ln(ktk) + ((R * T)/btk) * ln(ce)',
            description='Test Linearization',
            parameters={"x": "ln(ce)", "y": "qe", "m": "((R * T)/btk)", "b": "((R * T)/btk) * ln(ktk)"},
            latex_formula='',
            model_id=1,
            constants={'R': R_CONSTANT * (10 **-3), 'T': self.sample.temperature}
        )

        ce_transformed = np.log(np.array(self.sample.ce))
        qe_transformed = np.array(self.sample.qe)
        ce_transformed = np.nan_to_num(ce_transformed, nan=0.0, posinf=0.0, neginf=0.0)
        qe_transformed = np.nan_to_num(qe_transformed, nan=0.0, posinf=0.0, neginf=0.0)

        m = 0.015138
        b = 0.112385

        btk = (R_CONSTANT * (10 **-3) * self.sample.temperature) / m
        ktk = np.exp(((b * btk) / (R_CONSTANT * (10 **-3) * self.sample.temperature)))

        result = linearization.run(self.sample, {'R': R_CONSTANT * (10 **-3), 'T': self.sample.temperature} )
        # Validamos que se calculó correctamente la pendiente y la intersección
        self.assertAlmostEqual(result["slope"], m, delta=0.0001)
        self.assertAlmostEqual(result["intercept"], b, delta=0.0001)
        self.assertAlmostEqual(result["params_info"][0]["btk"], btk, delta=0.01)
        self.assertAlmostEqual(result["params_info"][0]["ktk"], ktk, delta=1.5)

        # Validamos que los puntos transformados sean correctos
        self.assertEqual(result["x"], round_list_numbers(ce_transformed.tolist()), ROUND_DIGIT)
        self.assertEqual(result["y"], round_list_numbers(qe_transformed.tolist()), ROUND_DIGIT)

        # Validamos el coeficiente de determinación R²
        self.assertAlmostEqual(result["statistics"]["r_squared"], 0.4483, delta=0.01)




if __name__ == '__main__':
    unittest.main()
