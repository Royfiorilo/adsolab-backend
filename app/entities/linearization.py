from scipy.stats import linregress
from sympy import symbols, Eq, solve, sympify

from .formula import Formula
from .model import Model


class Linearization(Model):
    def __init__(
            self,
            linearization_id,
            name,
            formula,
            description,
            parameters,
            model_id=None
    ):
        super().__init__(linearization_id, name, formula, description, parameters)
        self.model_id = model_id

    def calculate_dots(self, sample):
        x_dots, y_dots = [], []
        for ce, qe in zip(sample.ce, sample.qe):
            data = {"ce": ce, "qe": qe}
            x_funcion = Formula(self.parameters["x"])
            x_dots.append(x_funcion.apply(**data))
            y_funcion = Formula(self.parameters["y"])
            y_dots.append(y_funcion.apply(**data))
        return x_dots, y_dots


    def solve_equations(self, equations, unknown, slope, intercept):
        eq_m = Eq(sympify(equations['m']), slope)
        eq_b = Eq(sympify(equations['b']), intercept)
        solutions = solve((eq_m, eq_b), tuple(unknown))
        solutions_dict = [{var.name: float(sol) for var, sol in zip(unknown, sol_tuple)} for sol_tuple in solutions]
        return solutions_dict

    def format_solution(self, x_dots, y_dots, slope, intercept, r_value, std_err, solutions_dict, vars):
        return {
            "name": self.name,
            "transformed": {"x": x_dots, "y": y_dots},
            "slope": slope,
            "intercept": intercept,
            "statistics": {"r": r_value, "std_err": std_err},
            "parameters": [{"name": var, "value": solutions_dict[0][var]} for var in vars]
        }

    def run(self, *args):
        sample = args[0]
        x_dots, y_dots = self.calculate_dots(sample)
        slope, intercept, r_value, p_value, std_err = linregress(x_dots, y_dots)

        equations = {key: value for key, value in self.parameters.items() if key not in ['x', 'y']}
        variables = self.formula.get_variables()
        vars = [x.name for x in variables if x.name not in ['ce', 'qe']]
        unknown = symbols(vars)

        solutions_dict = self.solve_equations(equations, unknown,slope,intercept)
        return self.format_solution(x_dots, y_dots, slope, intercept, r_value, std_err, solutions_dict, vars)




