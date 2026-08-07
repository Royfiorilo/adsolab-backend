"""
kinetics_comparison_service.py

Responsabilidad:
    Comparar los modelos cinéticos ajustados por puntaje heurístico y por
    regresión Ridge sobre las predicciones combinadas.

    Espejo de `comparison_service.py` del módulo de equilibrio. La matemática es
    la misma (`AdsorptionModelComparison`), sólo cambian las variables: `time`/`qt`
    en lugar de `ce`/`qe`.
"""
from typing import Dict, List, Tuple

from entities.comparator import AdsorptionModelComparison
from utils import filter_negative, round_number


def _extract_best_methods(fitted_models: List[Tuple]) -> List[Dict]:
    """Descarta los modelos que no lograron ningún ajuste exitoso."""
    extracted = []
    for kinetic_model, model_id in fitted_models:
        best = kinetic_model.get_best_method()
        if best is None:
            continue
        extracted.append({"model_id": model_id, "best": best})
    return extracted


def determine_kinetic_heuristic_scores(best_methods: List[Dict]) -> Tuple[Dict, int]:
    compare_data = [
        {"statistics": item["best"].statistics, "residuals": item["best"].residuals, "name": item["model_id"]}
        for item in best_methods
    ]
    scores = AdsorptionModelComparison.determine_heuristic_scores_models(compare_data, "name")
    return scores, max(scores, key=scores.get)


def get_kinetic_ml_comparison(best_methods: List[Dict], sample) -> Dict:
    """
    Combina las predicciones de los modelos ajustados mediante Ridge para estimar
    pesos relativos.

    Se lee `transformed["qt_pred"]` directamente en lugar de `FitResult.get_qe_pred()`,
    que busca la clave `qe_pred` del módulo de equilibrio. Depende de correr antes de
    `ResponseFormatter.format_fit_result`, que descarta `qt_pred`.
    """
    qt_preds = [item["best"].transformed["qt_pred"] for item in best_methods]
    extended_preds = [item["best"].transformed["y"] for item in best_methods]
    extended_time = best_methods[0]["best"].transformed["x"]

    ridge_scores = AdsorptionModelComparison.get_ml_coefs_models(sample.qt, qt_preds, extended_preds)
    coefficients = ridge_scores["coefs"]

    results = [
        {"model": item["model_id"], "coef": coef}
        for item, coef in zip(best_methods, coefficients)
    ]
    best_model = results[coefficients.index(max(coefficients))]["model"]

    # En t = 0 no hay adsorción, así que la curva combinada arranca en 0 (misma
    # convención que equilibrio con ce = 0).
    curve = list(ridge_scores["y_pred"])
    curve[0] = 0

    return {
        "best_model": best_model,
        "transformed": filter_negative(extended_time, curve),
        "statistics": ridge_scores["statistics"],
        "residuals": ridge_scores["residuals"],
        "results": results,
    }


def get_kinetic_comparison(fitted_models: List[Tuple], sample) -> Dict:
    """
    Punto de entrada del servicio de comparación cinética.

    `fitted_models` es una lista de tuplas (KineticNoLinearModel, model_id).
    """
    best_methods = _extract_best_methods(fitted_models)
    if not best_methods:
        return {"heuristic": None, "ml": None}

    scores, best_heuristic = determine_kinetic_heuristic_scores(best_methods)

    return {
        "heuristic": {
            "best_model": best_heuristic,
            "results": [
                {"model": model, "score": round_number(score)}
                for model, score in scores.items()
            ],
        },
        "ml": get_kinetic_ml_comparison(best_methods, sample),
    }
