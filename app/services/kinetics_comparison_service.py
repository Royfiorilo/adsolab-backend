"""
kinetics_comparison_service.py

Responsabilidad:
    Comparar los modelos cinéticos ajustados usando criterios estadísticos
    (puntaje heurístico) y opcionalmente regresión Ridge (ML).

    Espejo de `comparison_service.py` del módulo de equilibrio, adaptado al
    contexto cinético. Los pesos y criterios de comparación pueden diferir
    de los del módulo de equilibrio según decisión de Jorge/Silvia.

    TODO: implementar la lógica de puntuación una vez que el ajuste no lineal
    cinético esté definido y los criterios estadísticos sean validados.
"""
from typing import List, Dict, Tuple

from entities.comparator import AdsorptionModelComparison
from utils import round_number


def determine_kinetic_heuristic_scores(fitted_models: List[Dict]) -> Dict:
    """
    Calcula un puntaje heurístico para cada modelo cinético ajustado.

    Criterios preliminares (idénticos al módulo de equilibrio, sujetos a ajuste):
      - R² Ajustado : 30 %
      - RMSE        : 30 %
      - AIC         : 25 %
      - Chi²        : 10 %
      - Bonos por análisis de residuos (normalidad, homocedasticidad,
        independencia): 5 % c/u

    TODO: implementar cálculo real.

    Returns:
        Dict con 'best_model' y 'scores' por modelo.
    """
    raise NotImplementedError(
        "determine_kinetic_heuristic_scores: pending implementation."
    )


def get_kinetic_ml_comparison(fitted_models: List[Dict], sample_time, sample_qt) -> Dict:
    """
    Combina las predicciones de todos los modelos cinéticos ajustados mediante
    Ridge Regression para estimar pesos relativos.

    Equivalente a `get_ml_coefs_models` de `comparison_service.py`.

    TODO: implementar una vez que el ajuste no lineal cinético esté disponible.

    Returns:
        Dict con coeficientes Ridge por modelo.
    """
    raise NotImplementedError(
        "get_kinetic_ml_comparison: pending implementation."
    )


def get_kinetic_comparison(fitted_models: List[Tuple], sample) -> Dict:
    """
    Punto de entrada del servicio de comparación cinética.
    Ejecuta heurística y (opcionalmente) ML.

    `fitted_models` es una lista de tuplas (KineticNoLinearModel, model_id).
    ML queda como None hasta que se valide con Jorge/Silvia.
    """
    if not fitted_models:
        return {"heuristic": None, "ml": None}

    compare_data = []
    for kinetic_model, model_id in fitted_models:
        best = kinetic_model.get_best_method()
        if best is None:
            continue
        compare_data.append({
            "statistics": best.statistics,
            "residuals": best.residuals,
            "name": model_id,
        })

    if not compare_data:
        return {"heuristic": None, "ml": None}

    scores = AdsorptionModelComparison.determine_heuristic_scores_models(compare_data, "name")
    best_model = max(scores, key=scores.get)

    return {
        "heuristic": {
            "best_model": best_model,
            "results": [
                {"model": model, "score": round_number(score)}
                for model, score in scores.items()
            ],
        },
        "ml": None,
    }
