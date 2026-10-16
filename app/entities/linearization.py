from scipy.stats import linregress
from sympy import Eq, solve, sympify, symbols

from .formula import Formula
from .linear_fit_errors import line_covariance, propagate_std_errors
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
            latex_formula,
            constants = [],
            model_id=None
    ):
        super().__init__(linearization_id, name, formula, description, parameters, latex_formula,constants)
        self.model_id = model_id

    def _calculate_dots(self, sample):
        x_dots, y_dots = [], []
        x_function = Formula(self.parameters["x"])
        y_function = Formula(self.parameters["y"])

        for ce, qe in zip(sample.ce, sample.qe):
            data = {"ce": ce, "qe": qe}

            # Si algún punto tiene algún valor en 0, no se hace la transformación.
            if data["ce"] != 0:
                x_dots.append(round(x_function.apply(**data), ROUND_DIGIT))
            else:
                x_dots.append(round(data["ce"], ROUND_DIGIT))
            if data["qe"] != 0:
                y_dots.append(round(y_function.apply(**data), ROUND_DIGIT))
            else:
                y_dots.append(round(data["qe"], ROUND_DIGIT))
        return x_dots, y_dots

    def _find_params_errors(self, params_values, result_lreg, eq_m, eq_b, x_dots):
        return propagate_std_errors(eq_m.lhs, eq_b.lhs, params_values, line_covariance(result_lreg, x_dots))


    def _find_params_values(self, equations, unknown, result_lreg, constants, x_dots):
        m_ecuation = equations['m']
        b_ecuation = equations['b']
        for constant in self.constants:
            value = constants[constant]
            if isinstance(value, (int, float)):
                m_ecuation = m_ecuation.replace(constant, str(value))
                b_ecuation = b_ecuation.replace(constant, str(value))
            else:
                raise ValueError(f"Constant {constant} must be int or float")

        eq_m = Eq(sympify(m_ecuation, evaluate=False), result_lreg.slope)
        eq_b = Eq(sympify(b_ecuation, evaluate=False), result_lreg.intercept)
        solutions = solve((eq_m, eq_b), tuple(unknown))
        params_info = [{var.name: float(sol) for var, sol in zip(unknown, sol_tuple)} for sol_tuple in solutions]

        parameter_std_errs = self._find_params_errors(params_info[0], result_lreg, eq_m, eq_b, x_dots)

        params_info.append(parameter_std_errs)

        return params_info


    def run(self, *args):
        sample = args[0]
        constants = args[1]

        # Transformamos los puntos para realizar la regresión lineal sobre esos puntos.
        x_dots, y_dots = self._calculate_dots(sample)

        # Ejecutar regresión lineal, guardando el resultado completo como result_lr
        try:
            result_lr = linregress(x_dots, y_dots)
        except ValueError as e:
            return {"name": self.name, "status": "ERROR", "reason": str(e)}

        # Obtenemos las ecuaciones que van a ser utilizadas para resolver el esquema de ecuaciones para despejar los
        # parámetros
        equations = {key: value for key, value in self.parameters.items() if key not in ['x', 'y']}
        if 'm' not in equations or 'b' not in equations:
            raise KeyError("The equations to solve the slope and/or y-intercept are not defined in the linearization.")

        # Transforma los parámetros a descubrir en incógnitas.
        variables = self.formula.get_variables()
        vars = [x.name for x in variables if (x.name not in ['ce', 'qe'])  and  (x.name not in self.constants)]
        unkown = symbols(vars)

        # Ejecuta el sistema de ecuaciones para descubrir el valor de los parámetros y su desvío estándar.
        params_info = self._find_params_values(equations, unkown, result_lr, constants, x_dots)

        result = {
            "name": self.name,
            "id": self._id,
            "x": x_dots,
            "y": y_dots,
            "slope": result_lr.slope,
            "intercept": result_lr.intercept,
            "vars": vars,
            "params_info": params_info,
            "statistics": {"r_squared": round(result_lr.rvalue, ROUND_DIGIT)},
        }

        return result

