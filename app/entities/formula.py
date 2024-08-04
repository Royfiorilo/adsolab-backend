from typing import List

from sympy import sympify, lambdify
import sympy as sp

class Formula:

    def __init__(self, formula_str):
        self.formula_str = formula_str
        if '=' in formula_str:
            formula_str = formula_str.split('=')[1].strip()
        self.formula = sympify(formula_str)
        self.variables = sorted(self.formula.free_symbols, key=lambda s: s.name)
        self.function = lambdify(self.variables, self.formula)

    def to_function(self):
        return self.function

    def apply(self, **kargs):
        args = []
        for variable in self.variables:
            if variable.name in kargs:
                args.append(kargs[variable.name])
        return self.function(*args)
