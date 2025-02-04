from typing import List, Dict, TypedDict
from entities.comparator import AdsorptionModelComparison
from utils import round_number


class ModelMethod(TypedDict):
    statistics: dict
    residuals: list
    name: str


class ModelComparison(TypedDict):
    heuristic: dict
    ridge: dict


def extract_method_data(models: list, results: list):
    compare_data = []
    qe_predictions = []
    y_predictions = []

    for model, result in zip(models, results):
        best_method = model.get_best_method()
        compare_data.append({
            "statistics": best_method.statistics,
            "name": result["model"],
            "residuals": best_method.residuals
        })
        qe_predictions.append(best_method.get_qe_pred())
        y_predictions.append(best_method.get_y())

    return compare_data, qe_predictions, y_predictions


def calculate_heuristic_scores(compare_data: List[ModelMethod]):
    scores = AdsorptionModelComparison.determine_heuristic_scores_models(compare_data, "name")
    best_model = max(scores, key=scores.get)
    return scores, best_model


def calculate_ridge_scores(models: list, y: List[float], qe_preds: List[float],
                           y_preds: List[float]) -> tuple[dict, str, List[dict]]:
    """
    Calculate ridge regression scores for models.
    """
    ridge_scores = AdsorptionModelComparison.get_ml_coefs_models(y, qe_preds, y_preds)
    coefficients = ridge_scores['coefs']

    model_results = [
        {'model': model._id, 'coef': coef}
        for model, coef in zip(models, coefficients)
    ]

    max_coef = max(coefficients)
    best_model_index = coefficients.index(max_coef)
    best_model = model_results[best_model_index]['model']

    return ridge_scores, best_model, model_results


def format_comparison_results(heuristic_scores, best_heuristic: str,
                              ridge_scores: dict, best_ridge: str,
                              model_results_ridge) -> ModelComparison:
    return {
        "heuristic": {
            "best_model": best_heuristic,
            "results": [
                {'model': model, 'score': round_number(score)}
                for model, score in heuristic_scores.items()
            ]
        },
        "ridge": {
            "best_model": best_ridge,
            "y_pred": ridge_scores['y_pred'],
            "statistics": ridge_scores['statistics'],
            "residuals": ridge_scores['residuals'],
            "results": model_results_ridge
        }
    }


def get_comparison(results: list, models: list, y) -> ModelComparison:
    compare_data, qe_preds, y_preds = extract_method_data(models, results)

    heuristic_scores, best_heuristic = calculate_heuristic_scores(compare_data)

    ridge_scores, best_ridge, model_results_ridge = calculate_ridge_scores(models, y, qe_preds, y_preds)

    return format_comparison_results(heuristic_scores, best_heuristic,ridge_scores, best_ridge, model_results_ridge)