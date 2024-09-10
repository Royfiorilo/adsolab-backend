import unittest
from entities.formula import Formula
import math


class FormulaApplyTest(unittest.TestCase):

    def setUp(self):
        self.sum_formula = Formula("a + b")
        self.multiply_formula = Formula("a * b")
        self.divide_formula = Formula("a / b")
        self.power_formula = Formula("a ** b")
        self.log_formula = Formula("log(a)")
        self.log_formula_base = Formula("log(a, n)")
        self.langmuir_formula = Formula("qe = qmax * k * ce / (1 + (k * ce))")
        self.freundlich_formula = Formula("qe = kf * ce**(1 /nf)")

    def test_sum_formula(self):
        sum_args = {"a": 1, "b": 2}
        self.assertEqual(self.sum_formula.apply(**sum_args), 3)
        sum_args = {"a": 1.3, "b": 2.4}
        self.assertEqual(self.sum_formula.apply(**sum_args), 3.7)
        sum_args = {"a": -3, "b": -9}
        self.assertEqual(self.sum_formula.apply(**sum_args), -12)

    def test_multiply_formula(self):
        mult_args = {"a": 3, "b": 3}
        self.assertEqual(self.multiply_formula.apply(**mult_args), 9)
        mult_args = {"a": 0.5, "b": 0.02}
        self.assertEqual(self.multiply_formula.apply(**mult_args), 0.01)
        mult_args = {"a": -3, "b": -4}
        self.assertEqual(self.multiply_formula.apply(**mult_args), 12)
        mult_args = {"a": -2, "b": 0.45}
        self.assertEqual(self.multiply_formula.apply(**mult_args), -0.9)

    def test_divide_formula(self):
        div_args = {"a": 1, "b": 2}
        self.assertEqual(self.divide_formula.apply(**div_args), 0.5)
        div_args = {"a": 1.3, "b": 2.4}
        self.assertAlmostEqual(self.divide_formula.apply(**div_args), 0.5416, 3)
        div_args = {"a": 0.5, "b": 2}
        self.assertEqual(self.divide_formula.apply(**div_args), 0.25)
        div_args = {"a": -4, "b": -2}
        self.assertEqual(self.divide_formula.apply(**div_args), 2)
        div_args = {"a": 0.5, "b": 0.5}
        self.assertEqual(self.divide_formula.apply(**div_args), 1)
        div_args = {"a": 0.5, "b": 0.05}
        self.assertEqual(self.divide_formula.apply(**div_args), 10)

    def test_log_formula(self):
        log_args = {"a": 1}
        self.assertAlmostEqual(self.log_formula.apply(**log_args), 0, places=4)
        log_args = {"a": math.e}
        self.assertAlmostEqual(self.log_formula.apply(**log_args), 1, places=4)
        log_args = {"a": math.e ** 2}
        self.assertAlmostEqual(self.log_formula.apply(**log_args), 2, places=4)
        log_args = {"a": math.e ** 3}
        self.assertAlmostEqual(self.log_formula.apply(**log_args), 3, places=4)

    def test_log_formula_base2(self):
        log_args = {"a": 1, "n": 2}
        self.assertAlmostEqual(self.log_formula_base.apply(**log_args), 0, places=4)
        log_args = {"a": 2, "n": 2}
        self.assertAlmostEqual(self.log_formula_base.apply(**log_args), 1, places=4)
        log_args = {"a": 4, "n": 2}
        self.assertAlmostEqual(self.log_formula_base.apply(**log_args), 2, places=4)
        log_args = {"a": 8, "n": 2}
        self.assertAlmostEqual(self.log_formula_base.apply(**log_args), 3, places=4)
        log_args = {"a": 1024, "n": 2}
        self.assertAlmostEqual(self.log_formula_base.apply(**log_args), 10, places=4)
        log_args = {"a": 2048, "n": 2}
        self.assertAlmostEqual(self.log_formula_base.apply(**log_args), 11, places=4)
        log_args = {"a": 4096, "n": 2}
        self.assertAlmostEqual(self.log_formula_base.apply(**log_args), 12, places=4)

    def test_log_formula_base10(self):
        log_args = {"a": 1, "n": 10}
        self.assertAlmostEqual(self.log_formula_base.apply(**log_args), 0, places=4)
        log_args = {"a": 10, "n": 10}
        self.assertAlmostEqual(self.log_formula_base.apply(**log_args), 1, places=4)
        log_args = {"a": 100, "n": 10}
        self.assertAlmostEqual(self.log_formula_base.apply(**log_args), 2, places=4)
        log_args = {"a": 1000, "n": 10}
        self.assertAlmostEqual(self.log_formula_base.apply(**log_args), 3, places=4)
        log_args = {"a": 0.1, "n": 10}
        self.assertAlmostEqual(self.log_formula_base.apply(**log_args), -1, places=4)
        log_args = {"a": 0.01, "n": 10}
        self.assertAlmostEqual(self.log_formula_base.apply(**log_args), -2, places=4)
        log_args = {"a": 0.001, "n": 10}
        self.assertAlmostEqual(self.log_formula_base.apply(**log_args), -3, places=4)

    def test_power_formula(self):
        power_args = {"a": 1, "b": 2}
        self.assertEqual(self.power_formula.apply(**power_args), 1)
        power_args = {"a": 1, "b": 0}
        self.assertEqual(self.power_formula.apply(**power_args), 1)
        power_args = {"a": 2, "b": 1}
        self.assertEqual(self.power_formula.apply(**power_args), 2)
        power_args = {"a": 2, "b": 4}
        self.assertEqual(self.power_formula.apply(**power_args), 16)
        power_args = {"a": 0.5, "b": 2}
        self.assertEqual(self.power_formula.apply(**power_args), 0.25)
        power_args = {"a": 4, "b": 0.5}
        self.assertEqual(self.power_formula.apply(**power_args), 2)

    def test_langmuir_formula(self):
        langmuir_args = {"ce": 1.0, "qmax": 10, "k": 0.5}
        self.assertAlmostEqual(self.langmuir_formula.apply(**langmuir_args), 3.3333, places=4)
        langmuir_args = {"ce": 1.0, "qmax": 10, "k": 1}
        self.assertAlmostEqual(self.langmuir_formula.apply(**langmuir_args), 5.0, places=4)
        langmuir_args = {"ce": 1.0, "qmax": 10, "k": 0.1}
        self.assertAlmostEqual(self.langmuir_formula.apply(**langmuir_args), 0.9091, places=4)
        langmuir_args = {"ce": 2.0, "qmax": 10, "k": 0.5}
        self.assertAlmostEqual(self.langmuir_formula.apply(**langmuir_args), 5, places=4)
        langmuir_args = {"ce": 0.5, "qmax": 10, "k": 0.5}
        self.assertAlmostEqual(self.langmuir_formula.apply(**langmuir_args), 2, places=4)

    def test_formula_freundlich(self):
        freundlich_args = {"ce": 1.0, "kf": 2, "nf": 2}
        self.assertAlmostEqual(self.freundlich_formula.apply(**freundlich_args), 2.0, places=4)
        freundlich_args = {"ce": 4.0, "kf": 2, "nf": 2}
        self.assertAlmostEqual(self.freundlich_formula.apply(**freundlich_args), 4.0, places=4)
        freundlich_args = {"ce": 1.0, "kf": 3, "nf": 3}
        self.assertAlmostEqual(self.freundlich_formula.apply(**freundlich_args), 3.0, places=4)
        freundlich_args = {"ce": 8.0, "kf": 1, "nf": 3}
        self.assertAlmostEqual(self.freundlich_formula.apply(**freundlich_args), 2.0, places=4)
        freundlich_args = {"ce": 27.0, "kf": 2, "nf": 3}
        self.assertAlmostEqual(self.freundlich_formula.apply(**freundlich_args), 6.0, places=4)


if __name__ == '__main__':
    unittest.main()
