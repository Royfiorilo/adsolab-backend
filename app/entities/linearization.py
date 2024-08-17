from scipy.stats import linregress
from sympy import symbols, Eq, solve, sympify

from .formula import Formula
from .model import Model


class Linearization(Model):
    def __init__(
            self,
            _id,
            name,
            formula,
            description,
            parameters,
            model_id=None
    ):
        super().__init__(_id, name, formula, description, parameters)
        self.model_id = model_id

    def run(self, *args):
        sample = args[0]
        x_dots, y_dots = [], []

        # Me armo el ce y qe como lo necesito para la funcion
        for ce, qe in zip(sample.ce, sample.qe):
            data = {"ce": ce, "qe": qe}

            x_funcion = Formula(self.parameters["x"])
            x_dots.append(x_funcion.apply(**data))
            y_funcion = Formula(self.parameters["y"])
            y_dots.append(y_funcion.apply(**data))

        slope, intercept, r_value, p_value, std_err = linregress(x_dots, y_dots)

        equations = {key: value for key, value in self.parameters.items() if not key == 'x' and not key == 'y'}

        variables = self.formula.get_variables()
        vars = [x.name for x in variables if x.name not in ['ce', 'qe']]

        unknown = symbols(vars)

        eq_m = Eq(sympify(equations['m']), slope)
        eq_b = Eq(sympify(equations['b']), intercept)

        solutions = solve((eq_m, eq_b), tuple(unknown))
        solutions_dict = [{var.name: float(sol) for var, sol in zip(unknown, sol_tuple)} for sol_tuple in solutions]
        print(solutions_dict[0])
        return solutions_dict[0]


