from dataclasses import dataclass
from typing import Dict, List, Any, Optional

import lmfit
import numpy as np
from numdifftools import Hessian

from entities.statistics import Statistics
from utils import round_number, round_list_numbers, filter_negative
from .comparator import AdsorptionModelComparison
from .model import Model

DEFAULT_ITERATIONS = 10000
DEFAULT_STEP = None
N_PARAM_ESTIMATED_SEED = 1.5
LIMIT_QMAX = 1.1
MIN_PARAM_VALUE = 0.001


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
    method_name: str
    parameters: List[Dict[str, Any]] = None
    raw_result: lmfit.model.ModelResult = None
    statistics: dict = None
    residuals: dict = None
    transformed: dict = None
    method_description: str = ""
    method_message: str = ""

    def get_y(self):
        return self.transformed.get("y")

    def get_qe_pred(self):
        return self.transformed.get("qe_pred")

    def clean_transformed(self, success: bool):
        if success:

            self.transformed = filter_negative(self.transformed.get("x").copy(), self.transformed.get("y").copy())
        else:
            if self.transformed:
                self.transformed = {"y": list(self.transformed.get("y")), "x": list(self.transformed.get("x"))}


class FitStrategy:
    def __init__(self, formula):
        self.model = lmfit.Model(formula.to_function(), independent_vars=['ce'])

    def fit(self, params: FitParameters) -> FitResult:
        parameters = self.model.make_params(**params.initial_params)

        is_temkin = False
        for param_name, param in parameters.items():
            min_val, max_val = MIN_PARAM_VALUE, np.inf
            if 'q' in param_name:
                max_val = params.qe.max() * LIMIT_QMAX
            elif "ktk" in param_name:
                min_val, max_val = 1, 10000
                is_temkin = True
            elif "btk" in param_name:
                min_val, max_val = MIN_PARAM_VALUE, LIMIT_QMAX
            param.set(min=min_val, max=max_val, brute_step=params.step)

        x = params.ce.copy()
        y = params.qe.copy()

        if  0 in params.ce and is_temkin:
            x = x[1:]
            y = y[1:]
        else:
            x[x == 0] = 1e-6

        result = self.model.fit(
            y,
            parameters,
            ce=x,
            method=params.method,
            nan_policy="omit",
            max_nfev=params.iterations
        )

        if is_temkin and 0 in params.ce :
            result.best_fit = np.insert(result.best_fit, 0, 0)

        return FitResult(
            success=bool(result.success),
            parameters=self._get_parameters_with_stderr(result),
            raw_result= result,
            method_name=params.method,
            method_message=str(result.message)
        )

    def _get_parameters_with_stderr(self, result):
        params = []
        for param, value in result.params.items():
            if value.stderr is None:
                try:
                    stderr = self._calculate_standard_errors(result)
                except Exception as e:
                    stderr = None
            else:
                stderr = value.stderr

            params.append({"name": param, "value": round_number(value.value), "std_err": round_number(stderr) if stderr else stderr})

        return params

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


class AdsorptionPredictor:
    def __init__(self, formula=None):
        self.formula = formula


    def predict(self, ce_values, parameters, extend=True, num_points=300):
        if extend:
            ce_values = self.extend_ce(ce_values, num_points)

        qe_pred = np.array([])
        try:
            for ce_val in ce_values:
                parameters["ce"] = ce_val
                if ce_val == 1e-10 or ce_val == 0:
                    qe = 0
                    ce_values[ce_values == 1e-10] = 0
                else:
                    qe = self.formula.apply(**parameters)
                qe_pred = np.append(qe_pred, qe)


        except Exception as e:
            print(e)

        return ce_values, round_list_numbers(qe_pred)

    def extend_ce(self, ce_values, num_points):
        min_ce, max_ce = 0, max(ce_values)
        linspace_values = np.linspace(min_ce, max_ce, num_points - len(ce_values))
        return np.union1d(linspace_values, ce_values)


class NoLinearModel(Model):
    def __init__(self, _id: str, name: str, formula, description: str, parameters, latex_formula, linearizations=None, constants: List[Any] = []):
        super().__init__(_id, name, formula, description, parameters, latex_formula)
        self.fit_strategy =  None
        self.adsorption_predictor = None
        self.linearizations = linearizations if linearizations is not None else []
        self.method_results: List[FitResult] = []
        self.best_method = None
        self.constants = constants or []


    def run(self, sample, seeds, methods, constants:{}, step: DEFAULT_STEP, iterations: DEFAULT_ITERATIONS)  -> List[FitResult]:
        x = np.array(sample.ce)
        y = np.array(sample.qe)


        iterations = DEFAULT_ITERATIONS if iterations is None else iterations
        initial_params = self._prepare_initial_params(seeds)
        self.initialize_with_constants(constants=constants)
        self.method_results = []


        for method, description in methods.items():
            try:
                result = self._run_method(x, y, initial_params, method, description, step, iterations)
            except Exception as e:
                print(f"Método {method} falló: {str(e)}")
                result = FitResult(
                    success = False,
                    method_message= str(e),
                    method_name= method,
                    method_description= description
                )
            self.method_results.append(result)

        self._determine_best_method()

        return self.method_results

    def initialize_with_constants(self, constants):
        if self.constants:
            self.formula.replace_constants(constants)
        self.fit_strategy = FitStrategy(self.formula)
        self.adsorption_predictor = AdsorptionPredictor(self.formula)

    def _prepare_initial_params(self, seeds) :
        return {param["name"]: param["value"] for param in seeds}

    def _run_method(self, x: np.ndarray, y: np.ndarray, initial_params, method, description, step,
                    iterations) -> FitResult:

        fit_params = FitParameters(x, y, initial_params, step, iterations, method)
        fit_result = self.fit_strategy.fit(fit_params)
        fit_result.method_description = description

        qe_pred = fit_result.raw_result.best_fit
        residuals = y - qe_pred

        params_dict = {p["name"]: p["value"] for p in fit_result.parameters}
        extended_ce, extended_qe = self.adsorption_predictor.predict(x, params_dict)


        transformed_data = {
            "x": extended_ce,
            "y": round_list_numbers(extended_qe),
            "qe_pred": round_list_numbers(qe_pred.tolist())
        }
        fit_result.statistics = Statistics.all_statistics(y, qe_pred,
                                                          len(fit_result.parameters),
                                                          float(fit_result.raw_result.aic),
                                                       float(fit_result.raw_result.bic))

        fit_result.residuals =  {"values": residuals.tolist(), "analysis": Statistics.check_residuals(residuals)}
        fit_result.transformed = transformed_data

        return fit_result

    def _determine_best_method(self):
        if not self.method_results:
            return
        success_methods = [method for method in self.method_results if method.success == True]
        results = [
            {
                "statistics": method.statistics,
                "residuals": method.residuals,
                "name": method.method_name
            }
            for method in success_methods
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

    def calculate_seeds(self, sample):
        seeds = []
        for parameter in self.parameters:
            seed = {}
            if "q" in parameter:
                seed['name'] = parameter
                seed['value'] = max(sample.qe)
            elif "k" in parameter:
                qhalf = max(sample.qe) / 2
                qe = min(sample.qe, key=lambda x: abs(x - qhalf))
                index = sample.qe.index(qe)
                ce_half = sample.ce[index]
                seed['name'] = parameter
                seed['value'] = round_number(1 / ce_half)
            elif "n" in parameter:
                seed['name'] = parameter
                seed['value'] = N_PARAM_ESTIMATED_SEED
            seeds.append(seed)

        return seeds

