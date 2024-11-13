from typing import Dict, List, Any

import numpy as np
import lmfit
from .model import Model


class NoLinearModel(Model):

    def __init__(
            self,
            _id,
            name,
            formula,
            description,
            parameters,
            linearizations=None
    ):
        super().__init__(_id, name, formula, description, parameters)
        if linearizations is None:
            linearizations = []
        self.linearizations = linearizations
        self.model = lmfit.Model(self.formula.to_function())
        self.method_results = []

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
                        initial_seeds: Dict[str, float]) -> list[Any]:

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

                stats_dict = self._calculate_all_statistics(y, y_pred, len(initial_seeds))

                self.method_results.append( {
                    'name': method,
                    'description': description,
                    'success': bool(result.success),
                    'params': dict(result.best_values),
                    'x': x.tolist(),
                    'y_pred': y_pred.tolist(),
                    'stats': stats_dict
                })

            except Exception as e:
                print(f"Método {method} falló: {str(e)}")

        return self.method_results

    def _calculate_all_statistics(self, y_true, y_pred, num_params):

        n = len(y_true)

        # SSE
        sse = np.sum((y_true - y_pred) ** 2)

        # TSS
        y_mean = np.mean(y_true)
        tss = np.sum((y_true - y_mean) ** 2)

        # R-cuadrado
        r_squared = 1 - (sse / tss)

        #  R-cuadrado ajustado
        r_squared_adj = 1 - (sse / tss) * ((n - 1) / (n - num_params - 1))

        # RMSE
        rmse = np.sqrt(sse / n)

        # Chi-cuadrado no lineal
        chi_squared = np.sum(((y_true - y_pred) ** 2) / np.abs(y_pred))

        # Chi-cuadrado reducido
        chi_squared_reduced = chi_squared / (n - num_params)

        #  HYBRID
        hybrid = (100 / (n - num_params)) * np.sum((y_true - y_pred) ** 2 / y_true) if n > 1 else None

        stderr = np.sqrt(sse / (n - num_params))
        cv_rmse = (rmse / np.mean(y_true)) * 100

        return {
            'R2': r_squared,
            'R2_adjusted': r_squared_adj,
            'Chi_squared': chi_squared,
            'Chi_squared_reduced': chi_squared_reduced,
            'SSE': sse,
            'RMSE': rmse,
            'HYBRID': hybrid,
            'Std_error': stderr,
            'CV_RMSE': cv_rmse,
            'n_points': n,
            'n_params': num_params
        }

    def get_seeds(self, parameters):
        seeds = {}
        for parameter in parameters:
            seeds[parameter["name"]] = parameter["value"]
        return seeds
