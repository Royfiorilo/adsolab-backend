from sympy import symbols, sympify, lambdify


class Formula:

    def __init__(self, formula_str):
        self.formula_str = formula_str
        self.formula = sympify(formula_str)
        self.variables = sorted(self.formula.free_symbols, key=lambda s: s.name)
        self.function = lambdify(self.variables, self.formula)

    def to_function(self):
        return self.function

    def apply(self, *args):
        return self.function(*args)
