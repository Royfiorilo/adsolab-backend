from typing import Dict

import numpy as np
import lmfit
from .model import Model
from .statistics import Statistics

class NoLinearModel(Model):

    def __init__(
            self,
            id,
            name,
            formula,
            description,
            parameters,
            linearizations=None
    ):
        super().__init__(id, name, formula, description, parameters)
        if linearizations is None:
            linearizations = []
        self.linearizations = linearizations
        self.model = lmfit.Model(self.formula.to_function())
        self.method_results = {}

    def has_linearizations(self):
        return len(self.linearizations) == 0

    def get_linearizations(self):
        return self.linearizations

    def run(self, *args):
        sample = args[0]
        x = np.array(sample.ce)
        y = np.array(sample.qe)
        seeds = self.get_seeds(args[1])

        return self.fit_all_methods(x, y, seeds)

    def fit_all_methods(self, x: np.array, y: np.array,
                        initial_seeds: Dict[str, float]) -> Dict[str, any]:

        params = self.model.make_params(**initial_seeds)

        methods = {
            'leastsq': 'Levenberg-Marquardt (Gauss-Newton modificado)',
            'cg': 'Gradiente Conjugado',
            'newton': 'Newton-CG',
            'cobyla': 'COBYLA'
        }

        for method, description in methods.items():
            try:
                result = self.model.fit(y, params, ce=x, method=method)

                y_pred = result.best_fit

                stats_dict = Statistics.all_statistics(y, y_pred, len(initial_seeds))

                self.method_results[method] = {
                    'description': description,
                    'success': bool(result.success),
                    'params': dict(result.best_values),
                    'AIC': float(result.aic),
                    'BIC': float(result.bic),
                    'stats': stats_dict
                }

            except Exception as e:
                print(f"Método {method} falló: {str(e)}")

        return self.method_results

    def get_seeds(self, parameters):
        seeds = {}
        for parameter in parameters:
            seeds[parameter["name"]] = parameter["value"]
        return seeds
