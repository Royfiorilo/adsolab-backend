"""
kinetics_comparison_service.py

Responsabilidad:
    Comparar los modelos cinéticos ajustados con dos criterios independientes:
    el puntaje heurístico y el error de predicción por validación cruzada
    (leave-one-out).

    El puntaje heurístico es el mismo de equilibrio (`AdsorptionModelComparison`).
    El segundo criterio difiere de equilibrio, que usa Ridge: con curvas casi
    colineales (PFO y PSO) Ridge elegía el modelo equivocado (ABE-002).
"""
from typing import Dict, List, Optional, Tuple

from entities.comparator import AdsorptionModelComparison
from utils import round_significant

ML_CRITERION = "loo_cv"


def _extract_best_methods(fitted_models: List[Tuple]) -> List[Dict]:
    """Descarta los modelos que no lograron ningún ajuste exitoso."""
    extracted = []
    for kinetic_model, model_id in fitted_models:
        best = kinetic_model.get_best_method()
        if best is None:
            continue
        extracted.append({"model_id": model_id, "best": best, "model": kinetic_model})
    return extracted


def determine_kinetic_heuristic_scores(best_methods: List[Dict]) -> Tuple[Dict, int]:
    compare_data = [
        {"statistics": item["best"].statistics, "residuals": item["best"].residuals, "name": item["model_id"]}
        for item in best_methods
    ]
    scores = AdsorptionModelComparison.determine_heuristic_scores_models(compare_data, "name")
    return scores, max(scores, key=scores.get)


def get_kinetic_ml_comparison(best_methods: List[Dict], sample) -> Optional[Dict]:
    """
    Segundo criterio: error de predicción leave-one-out de cada modelo.

    Cada modelo se reajusta sin un punto y predice ese punto; gana el de menor RMSE
    de esas predicciones. Los modelos cuyo reajuste falla quedan fuera; si ninguno
    se puede evaluar, devuelve None.
    """
    scored = []
    for item in best_methods:
        rmse = item["model"].loo_prediction_rmse(sample)
        if rmse is not None:
            scored.append((item["model_id"], rmse))
    if not scored:
        return None

    best_model = min(scored, key=lambda pair: pair[1])[0]
    return {
        "criterion": ML_CRITERION,
        "best_model": best_model,
        "results": [{"model": model_id, "cv_rmse": round_significant(rmse)} for model_id, rmse in scored],
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
                {"model": model, "score": round_significant(score)}
                for model, score in scores.items()
            ],
        },
        "ml": get_kinetic_ml_comparison(best_methods, sample),
    }
