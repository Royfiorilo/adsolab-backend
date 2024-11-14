from scipy.stats import linregress
from sympy import Eq, solve, sympify, symbols

from .formula import Formula
from .model import Model
from .statistics import Statistics

ROUND_DIGIT = 4

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

    def _calculate_dots(self, sample):
        x_dots, y_dots = [], []
        for ce, qe in zip(sample.ce, sample.qe):
            data = {"ce": ce, "qe": qe}
            x_function = Formula(self.parameters["x"])

            # Si algún punto tiene algún valor en 0, no se hace la transformación.
            if data["ce"] != 0:
                x_dots.append(round(x_function.apply(**data), ROUND_DIGIT))
            else:
                x_dots.append(round(data["ce"], ROUND_DIGIT))
            y_function = Formula(self.parameters["y"])
            if data["qe"] != 0:
                y_dots.append(round(y_function.apply(**data), ROUND_DIGIT))
            else:
                y_dots.append(round(data["qe"], ROUND_DIGIT))
        return x_dots, y_dots

    def _solve_equations(self, equations, unknown, slope, intercept):
        eq_m = Eq(sympify(equations['m']), slope)
        eq_b = Eq(sympify(equations['b']), intercept)
        solutions = solve((eq_m, eq_b), tuple(unknown))
        solutions_dict = [{var.name: float(sol) for var, sol in zip(unknown, sol_tuple)} for sol_tuple in solutions]
        return solutions_dict

    def run(self, *args):
        sample = args[0]
        # Transformamos los puntos para realizar la regresión lineal sobre esos puntos.
        x_dots, y_dots = self._calculate_dots(sample)
        try:
            slope, intercept, r_value, p_value, std_err = linregress(x_dots, y_dots)
        except ValueError as e:
            return {"name": self.name, "status": "ERROR", "reason": str(e)}

        # Obtenemos las ecuaciones que van a ser utilizadas para resolver el esquema de ecuaciones para despejar los
        # parámetros
        equations = {key: value for key, value in self.parameters.items() if key not in ['x', 'y']}
        if 'm' not in equations or 'b' not in equations:
            raise KeyError("The equations to solve the slope and/or y-intercept are not defined in the linearization.")

        variables = self.formula.get_variables()
        vars = [x.name for x in variables if x.name not in ['ce', 'qe']]
        unkown = symbols(vars)
        solutions_dict = self._solve_equations(equations, unkown, slope, intercept)

        result = {
            "name": self.name,
            "x": x_dots,
            "y": y_dots,
            "slope": slope,
            "intercept": intercept,
            "vars": vars,
            "solutions_dict": solutions_dict,
            "statistics": {"r_squared": round(Statistics.linear_r_squeared(r_value), ROUND_DIGIT), "std_err": round(std_err, ROUND_DIGIT)},
        }

        return result