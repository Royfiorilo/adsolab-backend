import numpy as np
from sympy import sympify, lambdify, Function

ln = Function("ln")


def _log(value, base=None):
    """`numpy.log` toma el 2do argumento posicional como array de salida, no como base."""
    if base is None:
        return np.log(value)
    return np.log(value) / np.log(base)


LAMBDIFY_MODULES = [{"log": _log, "ln": _log}, "numpy"]


class Formula:

    def __init__(self, formula_str):
        if '=' in formula_str:
            formula_str = formula_str.split('=')[1].strip()
        self.formula_str = formula_str
        self.formula = sympify(formula_str, locals={"ln": ln}, evaluate=False)
        self.variables = sorted(self.formula.free_symbols, key=lambda s: s.name)
        self.function = lambdify(self.variables, self.formula, modules=LAMBDIFY_MODULES)

    def to_function(self):
        return self.function

    def apply(self, **kargs):
        args = []
        for variable in self.variables:
            if variable.name in kargs:
                args.append(kargs[variable.name])
        return self.function(*args)

    def get_variables(self):
        return self.variables

    def replace_constants(self, constants):
        if not constants:
            return
        formula_str = self.formula_str
        for constant in constants:

            if isinstance(constants[constant], (int, float)):
                formula_str = formula_str.replace(constant, str(constants[constant]))
            else:
                raise ValueError(f"Constant {constant} must be int or float")

        self.formula = sympify(formula_str,locals={"ln": ln}, evaluate=False)
        self.variables = sorted(self.formula.free_symbols, key=lambda s: s.name)
        self.function = lambdify(self.variables, self.formula, modules=LAMBDIFY_MODULES)
