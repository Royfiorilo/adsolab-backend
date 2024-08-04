from scipy.stats import linregress

from entities.formula import Formula
from model import Model


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

        for ce, qe in zip(sample.ce, sample.qe):
            data = {"ce": ce, "qe": qe}

            x_funcion = Formula(self.parameters["x"])
            x_dots.append(x_funcion.apply(**data))
            y_funcion = Formula(self.parameters["y"])
            y_dots.append(y_funcion.apply(**data))

        slope, intercept, r_value, p_value, std_err = linregress(x_dots, y_dots)
