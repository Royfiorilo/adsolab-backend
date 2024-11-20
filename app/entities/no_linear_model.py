from typing import Dict, List, Any

import lmfit
import numpy as np
from sklearn.model_selection import LeaveOneOut, KFold

from utils import round_list_numbers
from .comparator import AdsorptionModelComparison
from .model import Model
from .statistics import Statistics


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

    def run(self, sample, parameters) -> dict[str, list[Any] | Any]:
        x = np.array(sample.ce)
        y = np.array(sample.qe)
        seeds = self.get_seeds(parameters)

        self.fit_all_methods(x, y, seeds)
        best_method = self.determine_best_method()


        return {
            "best_adjust": best_method,
            "adjustment_methods": self.method_results
        }


    def fit_all_methods(
            self, ce: np.array, qe: np.array, initial_seeds: Dict[str, float], cv_folds: int = 5
    ) :
        """
        Ajusta modelo usando varios metodos y hace ademas validacion cruzada
        """
        params = self.model.make_params(**initial_seeds)
        methods = self.get_optimization_methods()

        for method, description in methods.items():
            try:
                splits = self.get_cv_splits(ce, cv_folds)

                global_stats = self.evaluate_method(ce, qe, params, splits, method)


                best_performance = AdsorptionModelComparison.determine_best_model(global_stats, "fold_idx")

                self.method_results.append({
                    "name": method,
                    "description": description,
                    "best_performance": best_performance,
                    "folds": global_stats,
                })

            except Exception as e:
                print(f"Método {method} falló: {str(e)}")


    def get_seeds(self, parameters: List[Dict[str, Any]]) -> Dict[str, float]:
        return {param["name"]: param["value"] for param in parameters}

    def get_optimization_methods(self) -> Dict[str, str]:
        return {
            "leastsq": "Levenberg-Marquardt (Gauss-Newton modificado)",
            "cg": "Gradiente Conjugado",
            "newton": "Newton-CG",
            "cobyla": "COBYLA",
        }

    def get_cv_splits(self, ce: np.array, cv_folds: int) -> List[tuple]:
        if len(ce) >= 100:
            return list(KFold(n_splits=cv_folds, shuffle=True, random_state=42).split(ce))
        return list(LeaveOneOut().split(ce))


    def _evaluate_fit(
            self,
            ce_train: np.array,
            qe_train: np.array,
            params,
            method: str,
            fold_idx: str
    ) -> Dict[str, Any]:
        result = self.model.fit(qe_train, params, ce=ce_train, method=method, nan_policy='omit',  bounds=([0, 0], [np.inf, np.inf]))
        qe_pred = result.best_fit
        residuals = qe_train - qe_pred

        statistics = Statistics.all_statistics(
            qe_train, qe_pred, len(params), float(result.aic), float(result.bic)
        )

        return {
            "fold_idx": fold_idx,
            "transformed": {"x": ce_train.tolist(), "y": round_list_numbers(qe_pred.tolist())},
            "success": bool(result.success),
            "parameters": [
                {"name": k, "value": v} for k, v in result.best_values.items()
            ],
            "statistics": statistics,
            "residuals": Statistics.check_residuals(residuals),
        }


    def evaluate_method(
            self, ce: np.array, qe: np.array, params, splits: List[tuple], method: str
    ) -> List[Dict[str, Any]]:
        fold_stats = []

        for train_idx, test_idx in splits:
            ce_train = ce[train_idx]
            qe_train = qe[train_idx]

            fold_result = self._evaluate_fit(
                ce_train, qe_train, params, method, fold_idx=f"{train_idx} - {test_idx}"
            )
            fold_stats.append(fold_result)

        fold_stats.append(self._evaluate_fit(
            ce_train=ce,
            qe_train=qe,
            params=params,
            method=method,
            fold_idx="all"
        ))

        return fold_stats

    def determine_best_method(self):
        results = []
        best_fold = None
        for method in self.method_results:
            for fold in method["folds"]:
                if fold["fold_idx"] == method["best_performance"]:
                    best_fold = fold
                    self.best_method = fold
            results.append({ "statistics":best_fold["statistics"],
                             "residuals":best_fold["residuals"],
                             "name": method["name"]
                             })

        best_method = AdsorptionModelComparison.determine_best_model(results, "name")
        return best_method

    def get_best_method(self):
        return self.best_method