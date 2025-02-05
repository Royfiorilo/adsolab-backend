from dataclasses import dataclass
from typing import Dict, List, Any, Optional

import lmfit
import numpy as np
from numdifftools import Hessian

from entities.statistics import Statistics
from utils import round_number, round_list_numbers
from .comparator import AdsorptionModelComparison
from .model import Model

DEFAULT_ITERATIONS = 10000

@dataclass
class FitParameters:
    ce: np.ndarray
    qe: np.ndarray
    initial_params: dict
    step: Optional[float]
    iterations: int
    method: str


@dataclass
class FitResult:
    success: bool
    parameters: List[Dict[str, Any]]
    raw_result: lmfit.model.ModelResult
    method_name: str
    statistics: dict = None
    residuals: np.ndarray = None
    transformed: dict = None
    method_description: str = ""

    def get_y(self):
        return self.transformed.get("y")

    def get_qe_pred(self):
        return self.transformed.get("qe_pred")

    def clean_transformed(self):
        self.transformed = {"y":self.transformed.get("y"), "x":self.transformed.get("x")}


class FitStrategy:
    def __init__(self, formula):
        self.model = lmfit.Model(formula.to_function())

    def fit(self, params: FitParameters) -> FitResult:
        parameters = self.model.make_params(**params.initial_params)

        for param_name, param in parameters.items():
            param.set(min=0, max=np.inf, brute_step=params.step)

        result = self.model.fit(
            params.qe,
            parameters,
            ce=params.ce,
            method=params.method,
            nan_policy="omit",
            max_nfev=params.iterations
        )

        return FitResult(
            success=bool(result.success),
            parameters=self._get_parameters_with_stderr(result),
            raw_result=result,
            method_name=params.method
        )

    def _get_parameters_with_stderr(self, result: lmfit.model.ModelResult):
        return [
            {
                "name": name,
                "value": round_number(param.value),
                "std_err": round_number(param.stderr) if param.stderr else self._calculate_standard_errors(result)
            }
            for name, param in result.params.items()
        ]

    def _calculate_standard_errors(self, result):
        """
        Calculate standard errors for parameters using numerical Hessian.
        """
        param_values = np.array([p.value for p in result.params.values()])
        # Compute the Hessian matrix
        hessian_func = Hessian(lambda p: np.sum(result.residual ** 2))
        hessian_matrix = hessian_func(param_values)

        # Covariance matrix is the inverse of the Hessian
        covariance_matrix = np.linalg.inv(hessian_matrix)

        # Standard errors are the square roots of the diagonal elements
        return np.sqrt(np.diag(covariance_matrix))



class PointsExtender:
    def __init__(self, formula):
        self.formula = formula

    def extend(self, ce: np.ndarray, parameters: Dict[str, float], num_points: int = 300) -> (np.ndarray, np.ndarray):
        _min, _max = 0, ce.max()
        extended_ce = np.linspace(_min, _max, num_points)

        return extended_ce, np.array([
            self.formula.apply(**{**parameters, "ce": ce_val})
            for ce_val in extended_ce
        ])

class NoLinearModel(Model):
    def __init__(self, _id: str, name: str, formula, description: str, parameters, linearizations=None):
        super().__init__(_id, name, formula, description, parameters)
        self.fit_strategy =  FitStrategy(self.formula)
        self.points_extender = PointsExtender(self.formula)
        self.linearizations = linearizations if linearizations is not None else []
        self.method_results: List[FitResult] = []
        self.best_method = None

    def run(self, sample, seeds, methods, step, iterations) -> List[FitResult]:
        x = np.array(sample.ce)
        y = np.array(sample.qe)

        iterations = DEFAULT_ITERATIONS if iterations is None else iterations
        initial_params = self._prepare_initial_params(seeds)
        self.method_results = []

        for method, description in methods.items():
            try:
                result = self._run_method(x, y, initial_params, method, description, step, iterations)
                self.method_results.append(result)
            except Exception as e:
                print(f"Method {method} failed: {str(e)}")

        return self.method_results

    def _prepare_initial_params(self, seeds) :
        return {param["name"]: param["value"] for param in seeds}

    def _run_method( self, x: np.ndarray, y: np.ndarray, initial_params, method, description, step, iterations) -> FitResult:
        fit_params = FitParameters(x, y, initial_params, step, iterations, method)
        fit_result = self.fit_strategy.fit(fit_params)
        fit_result.method_description = description

        qe_pred = fit_result.raw_result.best_fit
        residuals = y - qe_pred


        params_dict = {p["name"]: p["value"] for p in fit_result.parameters}
        extended_ce, extended_qe = self.points_extender.extend(x, params_dict)
        self._determine_best_method()

        transformed_data = {
            "x": round_list_numbers(extended_ce.tolist()),
            "y": round_list_numbers(extended_qe.tolist()),
            "qe_pred": round_list_numbers( qe_pred.tolist())
        }
        fit_result.statistics = Statistics.all_statistics(y, qe_pred,
                                                          len(fit_result.parameters),
                                                          float(fit_result.raw_result.aic),
                                                          float(fit_result.raw_result.bic))
        fit_result.residuals =  Statistics.check_residuals(residuals)
        fit_result.transformed = transformed_data

        return fit_result

    def _determine_best_method(self):
        if not self.method_results:
            return
        results = [
            {
                "statistics": method.statistics,
                "residuals": method.residuals,
                "name": method.method_name
            }
            for method in self.method_results
        ]

        scores = AdsorptionModelComparison.determine_heuristic_scores_models(
            results, "name"
        )

        best_method = max(scores, key=scores.get)
        for method in self.method_results:
            if method.method_name == best_method:
                self.best_method = method



    def get_best_method(self) -> FitResult:
        return self.best_method

    def get_best_method_name(self) -> str:
        return self.best_method.method_name