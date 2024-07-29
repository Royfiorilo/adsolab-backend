import unittest
from app.entities.formula import Formula
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
        self.assertEqual(self.sum_formula.apply(1, 2), 3)
        self.assertEqual(self.sum_formula.apply(1.3, 2.4), 3.7)
        self.assertEqual(self.sum_formula.apply(-3, -9), -12)

    def test_multiply_formula(self):
        self.assertEqual(self.multiply_formula.apply(3, 3), 9)
        self.assertEqual(self.multiply_formula.apply(0.5, 0.02), 0.01)
        self.assertEqual(self.multiply_formula.apply(-3, -4), 12)
        self.assertEqual(self.multiply_formula.apply(-2, 0.45), -0.9)

    def test_divide_formula(self):
        self.assertEqual(self.divide_formula.apply(1, 2), 0.5)
        self.assertAlmostEqual(self.divide_formula.apply(1.3, 2.4), 0.5416, 3)
        self.assertEqual(self.divide_formula.apply(0.5, 2), 0.25)
        self.assertEqual(self.divide_formula.apply(-4, -2), 2)
        self.assertEqual(self.divide_formula.apply(0.5, 0.5), 1)
        self.assertEqual(self.divide_formula.apply(0.5, 0.05), 10)

    def test_log_formula(self):
        self.assertAlmostEqual(self.log_formula.apply(1), 0, places=4)
        self.assertAlmostEqual(self.log_formula.apply(math.e), 1, places=4)
        self.assertAlmostEqual(self.log_formula.apply(math.e ** 2), 2, places=4)
        self.assertAlmostEqual(self.log_formula.apply(math.e ** 3), 3, places=4)

    def test_log_formula_base2(self):
        self.assertAlmostEqual(self.log_formula_base.apply(1, 2), 0, places=4)
        self.assertAlmostEqual(self.log_formula_base.apply(2, 2), 1, places=4)
        self.assertAlmostEqual(self.log_formula_base.apply(4, 2), 2, places=4)
        self.assertAlmostEqual(self.log_formula_base.apply(8, 2), 3, places=4)
        self.assertAlmostEqual(self.log_formula_base.apply(16, 2), 4, places=4)
        self.assertAlmostEqual(self.log_formula_base.apply(1024, 2), 10, places=4)
        self.assertAlmostEqual(self.log_formula_base.apply(2048, 2), 11, places=4)
        self.assertAlmostEqual(self.log_formula_base.apply(4096, 2), 12, places=4)
    def test_log_formula_base10(self):
        self.assertAlmostEqual(self.log_formula_base.apply(1, 10), 0, places=4)
        self.assertAlmostEqual(self.log_formula_base.apply(10, 10), 1, places=4)
        self.assertAlmostEqual(self.log_formula_base.apply(100, 10), 2, places=4)
        self.assertAlmostEqual(self.log_formula_base.apply(1000, 10), 3, places=4)
        self.assertAlmostEqual(self.log_formula_base.apply(0.1, 10), -1, places=4)
        self.assertAlmostEqual(self.log_formula_base.apply(0.01, 10), -2, places=4)
        self.assertAlmostEqual(self.log_formula_base.apply(0.001, 10), -3, places=4)
    def test_power_formula(self):
        self.assertEqual(self.power_formula.apply(1, 2), 1)
        self.assertEqual(self.power_formula.apply(1, 0), 1)
        self.assertEqual(self.power_formula.apply(2, 1), 2)
        self.assertEqual(self.power_formula.apply(2, 4), 16)
        self.assertEqual(self.power_formula.apply(0.5, 2), 0.25)
        self.assertEqual(self.power_formula.apply(4, 0.5), 2)

    def test_langmuir_formula(self):
        self.assertAlmostEqual(self.langmuir_formula.apply(1.0, 0.5, 10), 3.3333, places=4)
        self.assertAlmostEqual(self.langmuir_formula.apply(1.0, 1, 10), 5.0, places=4)
        self.assertAlmostEqual(self.langmuir_formula.apply(1.0, 0.1, 10), 0.9091, places=4)
        self.assertAlmostEqual(self.langmuir_formula.apply(2.0, 0.5, 10), 5, places=4)
        self.assertAlmostEqual(self.langmuir_formula.apply(0.5, 0.5, 10), 2, places=4)

    def test_formula_freundlich(self):
        self.assertAlmostEqual(self.freundlich_formula.apply(1.0, 2, 2), 2.0, places=4)
        self.assertAlmostEqual(self.freundlich_formula.apply(4.0, 2, 2), 4.0, places=4)
        self.assertAlmostEqual(self.freundlich_formula.apply(1.0, 3, 3), 3.0, places=4)
        self.assertAlmostEqual(self.freundlich_formula.apply(8.0, 1, 3), 2.0, places=4)
        self.assertAlmostEqual(self.freundlich_formula.apply(27.0, 2, 3), 6.0, places=4)

if __name__ == '__main__':
    unittest.main()
