"""
kinetics_no_linear_model_service.py

Responsabilidad:
    Ejecutar el ajuste no lineal de modelos cinéticos usando `time` como
    variable independiente y `qt` como variable dependiente.

    Espejo directo de `no_linear_model_service.py` del módulo de equilibrio,
    con las siguientes diferencias clave:
      - Las variables de entrada son `time` / `qt` en lugar de `ce` / `qe`.
      - Los bounds y las semillas iniciales se adaptan a los parámetros
        típicos de modelos cinéticos (qe, k1, k2, kid, C, etc.).
      - Se reutiliza la infraestructura de `lmfit` y `scipy` idénticamente.

    TODO: implementar la lógica de ajuste una vez que las fórmulas definitivas
    de los modelos cinéticos sean validadas con Jorge/Silvia.
"""
from typing import List, Dict, Any

from entities.kinetics_sample import KineticsSampleEntity
from services.kinetics_model_service import find_kinetic_models


def calculate_kinetic_seeds(sample: KineticsSampleEntity, model_data: Dict[str, Any]) -> List[Dict]:
    """
    Genera semillas iniciales para los parámetros del modelo cinético.

    Estrategia por tipo de parámetro:
      - 'qe'  → max(qt)                  (capacidad de equilibrio aparente)
      - 'k1'  → 0.1                       (constante de velocidad PFO)
      - 'k2'  → 0.01                      (constante de velocidad PSO)
      - 'kid' → max(qt) / max(time)**0.5  (constante de difusión intraparticular)
      - default → 1.0

    TODO: refinar con base en análisis de los datos experimentales.
    """
    parameters = model_data.get('parameters', {})
    seeds = []
    max_qt = max(sample.qt) if sample.qt else 1.0
    max_time = max(sample.time) if sample.time else 1.0

    for param_name in parameters:
        name_lower = param_name.lower()
        if 'qe' in name_lower or name_lower.startswith('q'):
            value = max_qt
        elif name_lower in ('k1',):
            value = 0.1
        elif name_lower in ('k2',):
            value = 0.01
        elif name_lower in ('kid',):
            value = max_qt / (max_time ** 0.5) if max_time > 0 else 1.0
        else:
            value = 1.0
        seeds.append({"name": param_name, "value": round(value, 6)})

    return seeds


def predict_kinetic_seeds(request_json: dict) -> List[Dict]:
    """
    Calcula semillas iniciales para los modelos cinéticos solicitados.

    Equivalente a `predict_models_seeds` de `investigation_service.py`.
    """
    from services.kinetics_sample_service import find_kinetic_sample

    sample = find_kinetic_sample(request_json['kinetic_sample_id'])
    filter_indexes = request_json.get('filter', [])
    if filter_indexes:
        from services.kinetics_sample_service import filter_kinetic_sample
        sample = filter_kinetic_sample(sample, filter_indexes)

    all_models = {m['_id']: m for m in find_kinetic_models()}
    results = []

    for model_request in request_json['models']:
        model_id = model_request['model']
        model_data = all_models.get(model_id)
        if model_data is None:
            continue
        seeds = calculate_kinetic_seeds(sample, model_data)
        results.append({
            "id": model_id,
            "name": model_data.get('name'),
            "seeds": seeds,
        })

    return results


def run_kinetic_no_linear_models(request_json: dict):
    """
    Ejecuta el ajuste no lineal de uno o varios modelos cinéticos.

    Flujo (espejo de `run_no_linear_models` en `investigation_service.py`):
      1. Recuperar y filtrar muestra cinética.
      2. Para cada modelo: ejecutar ajuste con cada método de optimización.
      3. Seleccionar el mejor método por puntuación heurística.
      4. Calcular estadísticas y residuos.
      5. Generar curva extendida lista para Plotly.

    TODO: implementar una vez que los modelos cinéticos definitivos estén
    validados y se decida si se reutiliza la clase `FitStrategy` de
    `no_linear_model.py` o se crea una nueva.

    Returns:
        (results, comparison) donde:
          - results: lista de modelos ajustados con parámetros y estadísticas.
          - comparison: dict con heurística y ML.
    """
    raise NotImplementedError(
        "run_kinetic_no_linear_models: pending implementation after model validation."
    )
