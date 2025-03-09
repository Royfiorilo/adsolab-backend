import unittest
from entities.formula import Formula


def caller(func, *args):
    return func(*args)


class FormulaToFunctionTest(unittest.TestCase):

    def setUp(self):
        self.sum = Formula("a + b").to_function()
        self.langmuir_function = Formula("qe = qmax * k * ce / (1 + (k * ce))").to_function()
        self.freundlich_function = Formula("qe = kf * ce**(1 /nf)").to_function()

    def test_sum_function(self):
        self.assertEqual(self.sum(1, 2), 3)
        self.assertEqual(caller(self.sum, 1, 2), 3)

    def test_langmuir_function(self):
        self.assertAlmostEqual(self.langmuir_function(1.0, 0.5, 10), 3.3333, places=4)
        self.assertAlmostEqual(self.langmuir_function(1.0, 1, 10), 5.0, places=4)
        self.assertAlmostEqual(caller(self.langmuir_function, 1, 0.5, 10), 3.3333, places=4)
        self.assertAlmostEqual(caller(self.langmuir_function, 1, 1, 10), 5.0, places=4)

    def test_freundlich_function(self):
        self.assertAlmostEqual(self.freundlich_function(1.0, 2, 2), 2.0, places=4)
        self.assertAlmostEqual(self.freundlich_function(27.0, 2, 3), 6.0, places=4)
        self.assertAlmostEqual(caller(self.freundlich_function, 1.0, 2, 2), 2.0, places=4)
        self.assertAlmostEqual(caller(self.freundlich_function, 27.0, 2, 3), 6.0, places=4)

if __name__ == '__main__':
    unittest.main()
