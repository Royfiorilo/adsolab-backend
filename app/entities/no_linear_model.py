from typing import Dict, List, Any

import lmfit
import numpy as np
from numdifftools import Hessian

from utils import round_list_numbers, round_number
from .comparator import AdsorptionModelComparison
from .model import Model
from .statistics import Statistics

DEFAULT_ITERATIONS = 10000
DEFAULT_STEP = 0.1


class NoLinearModel(Model):

    def __init__(
            self,
            _id: str,
            name: str,
            formula: Any,
            description: str,
            parameters: List[Dict[str, Any]],
            linearizations: List[Any] = None,
    ):
        super().__init__(_id, name, formula, description, parameters)
        self.linearizations = linearizations or []
        self.model = lmfit.Model(self.formula.to_function())
        self.method_results = []
        self.best_method = None

    def has_linearizations(self) -> bool:
        return len(self.linearizations) > 0

    def get_linearizations(self) -> List[Any]:
        return self.linearizations

    def get_best_method(self):
        return self.best_method


    def _calculate_standard_errors(self, result, params):
        """
        Calculate standard errors for parameters using numerical Hessian.
        """
        # Compute the Hessian matrix
        hessian_func = Hessian(lambda p: np.sum(result['residuals'] ** 2))
        hessian_matrix = hessian_func(params)

        # Covariance matrix is the inverse of the Hessian
        covariance_matrix = np.linalg.inv(hessian_matrix)

        # Standard errors are the square roots of the diagonal elements
        return np.sqrt(np.diag(covariance_matrix))


    def _get_parameters_with_stderr(self, result):
        params = []

        for param, value in result.params.items():
            stderr = None
            if value.stderr is None:
                stderr = self._calculate_standard_errors(result, result.params)
            else:
                stderr = value.stderr

            params.append({"name": param, "value": round_number(value.value), "std_err": round_number(stderr)})

        return params

    def get_seeds(self, parameters: List[Dict[str, Any]]) -> Dict[str, float]:
        return {param["name"]: param["value"] for param in parameters}

    def run(self, sample, seeds, methods, step: None, iterations: None) -> dict[str, list[Any] | Any]:
        x = np.array(sample.ce)
        y = np.array(sample.qe)
        seeds = self.get_seeds(seeds)

        step = step if step is not None else DEFAULT_STEP
        iterations = iterations if iterations is not None else DEFAULT_ITERATIONS

        self.fit_all_methods(x, y, seeds, methods, step, iterations)
        best_method = self.determine_best_method()

        return {
            "best_adjust": best_method,
            "adjustment_methods": self.method_results
        }

    def fit_all_methods(
            self, ce: np.array, qe: np.array,
            initial_seeds: Dict[str, float], methods: Dict[str, str],
            step, iteration, cv_folds: int = 5
    ):
        """
        Ajusta modelo usando varios metodos y hace ademas validacion cruzada
        """
        params = self.model.make_params(**initial_seeds)

        for method, description in methods.items():
            try:
                result = self._evaluate_fit(ce, qe, params, step, iteration, method)
                result.update({"name": method, "description": description})
                self.method_results.append(result)
            except Exception as e:
                print(f"Método {method} falló: {str(e)}")

    def _evaluate_fit(
            self,
            ce: np.array,
            qe: np.array,
            params,
            step,
            iteration,
            method: str
    ) -> Dict[str, Any]:

        for param_name, param in params.items():
            param.set(min=0, max=np.inf, brute_step=step)

        result = self.model.fit(
            qe, params, ce=ce, method=method, nan_policy="omit", max_nfev=iteration)

        qe_pred = result.best_fit
        residuals = qe - qe_pred

        statistics = Statistics.all_statistics(
            qe, qe_pred, len(params), float(result.aic), float(result.bic)
        )


        return {
            "transformed": {"x": ce.tolist(), "y": round_list_numbers(qe_pred.tolist())},
            "success": bool(result.success),
            "parameters": self._get_parameters_with_stderr(result),
            "statistics": statistics,
            "residuals": Statistics.check_residuals(residuals),
        }

    def determine_best_method(self):
        results = []
        for method in self.method_results:
            results.append({"statistics": method["statistics"],
                            "residuals": method["residuals"],
                            "name": method["name"]
                            })

        scores = AdsorptionModelComparison.determine_heuristic_scores_models(results, "name")
        best_method = max(scores, key=scores.get)

        for method in self.method_results:
            if method["name"] == best_method:
                self.best_method = method
        return best_method
