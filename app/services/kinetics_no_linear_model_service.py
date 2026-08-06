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
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

import lmfit
import numpy as np

from entities.comparator import AdsorptionModelComparison
from entities.formula import Formula
from entities.kinetics_sample import KineticsSampleEntity
from entities.no_linear_model import FitResult, FitStrategy, MIN_PARAM_VALUE, LIMIT_QMAX, DEFAULT_ITERATIONS
from entities.response_formatter import ResponseFormatter
from entities.statistics import Statistics
from services.kinetics_model_service import find_kinetic_models, find_kinetic_model
from services.model_service import get_optimization_methods
from utils import round_list_numbers, round_number


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


@dataclass
class KineticFitParameters:
    time: np.ndarray
    qt: np.ndarray
    initial_params: dict
    step: Optional[float]
    iterations: int
    method: str


class KineticFitStrategy(FitStrategy):
    """FitStrategy adaptado para cinéticas: variable independiente `time` en lugar de `ce`."""

    def __init__(self, formula: Formula):
        self.model = lmfit.Model(formula.to_function(), independent_vars=['time'])

    def fit(self, params: KineticFitParameters) -> FitResult:
        parameters = self.model.make_params(**params.initial_params)

        for param_name, param in parameters.items():
            name_lower = param_name.lower()
            if 'q' in name_lower:
                param.set(min=MIN_PARAM_VALUE, max=params.qt.max() * LIMIT_QMAX)
            else:
                param.set(min=0, max=np.inf, brute_step=params.step)

        result = self.model.fit(
            params.qt,
            parameters,
            time=params.time,
            method=params.method,
            nan_policy="omit",
            max_nfev=params.iterations,
        )

        return FitResult(
            success=bool(result.success),
            parameters=self._get_parameters_with_stderr(result),
            raw_result=result,
            method_name=params.method,
            method_message=str(result.message),
        )


class KineticPredictor:
    def __init__(self, formula: Formula):
        self.formula = formula

    def predict(self, time_values: np.ndarray, parameters: dict, num_points: int = 300):
        extended_time = self._extend_time(time_values, num_points)
        qt_pred = np.array([
            self.formula.apply(**{**parameters, "time": float(t)})
            for t in extended_time
        ])
        return extended_time, round_list_numbers(qt_pred.tolist())

    def _extend_time(self, time_values: np.ndarray, num_points: int) -> np.ndarray:
        t_max = float(np.max(time_values))
        linspace_values = np.linspace(0, t_max, num_points - len(time_values))
        return np.union1d(linspace_values, time_values)


class KineticNoLinearModel:
    def __init__(self, model_data: dict):
        self.formula = Formula(model_data['formula'])
        self._id = model_data['_id']
        self.name = model_data['name']
        self.parameters = model_data.get('parameters', {})
        self.fit_strategy = KineticFitStrategy(self.formula)
        self.predictor = KineticPredictor(self.formula)
        self.method_results: List[FitResult] = []
        self.best_method: Optional[FitResult] = None

    def run(self, sample: KineticsSampleEntity, seeds: List[Dict],
            methods: Dict, step=None, iterations=None) -> List[FitResult]:
        x = np.array(sample.time, dtype=float)
        y = np.array(sample.qt, dtype=float)
        iterations = DEFAULT_ITERATIONS if iterations is None else iterations
        initial_params = {s['name']: s['value'] for s in seeds}
        self.method_results = []

        for method, description in methods.items():
            try:
                result = self._run_method(x, y, initial_params, method, description, step, iterations)
            except Exception as e:
                result = FitResult(
                    success=False,
                    method_message=str(e),
                    method_name=method,
                    method_description=description,
                )
            self.method_results.append(result)

        self._determine_best_method()
        return self.method_results

    def _run_method(self, x, y, initial_params, method, description, step, iterations) -> FitResult:
        fit_params = KineticFitParameters(x, y, initial_params, step, iterations, method)
        fit_result = self.fit_strategy.fit(fit_params)
        fit_result.method_description = description

        qt_pred = fit_result.raw_result.best_fit
        residuals = y - qt_pred
        params_dict = {p['name']: p['value'] for p in fit_result.parameters}
        extended_time, extended_qt = self.predictor.predict(x, params_dict)

        fit_result.statistics = Statistics.all_statistics(
            y, qt_pred,
            len(fit_result.parameters),
            float(fit_result.raw_result.aic),
            float(fit_result.raw_result.bic),
        )
        fit_result.residuals = {
            "values": residuals.tolist(),
            "analysis": Statistics.check_residuals(residuals),
        }
        fit_result.transformed = {
            "x": extended_time.tolist(),
            "y": extended_qt,
            "qt_pred": round_list_numbers(qt_pred.tolist()),
        }

        return fit_result

    def _determine_best_method(self):
        success_methods = [m for m in self.method_results if m.success]
        if not success_methods:
            return
        compare_data = [
            {"statistics": m.statistics, "residuals": m.residuals, "name": m.method_name}
            for m in success_methods
        ]
        scores = AdsorptionModelComparison.determine_heuristic_scores_models(compare_data, "name")
        best_name = max(scores, key=scores.get)
        for m in self.method_results:
            if m.method_name == best_name:
                self.best_method = m

    def get_best_method(self) -> Optional[FitResult]:
        return self.best_method

    def get_best_method_name(self) -> Optional[str]:
        return self.best_method.method_name if self.best_method else None


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
    from services.kinetics_sample_service import find_kinetic_sample, filter_kinetic_sample
    from services.kinetics_comparison_service import get_kinetic_comparison

    sample = find_kinetic_sample(request_json['kinetic_sample_id'])
    filter_indexes = request_json.get('filter', [])
    if filter_indexes:
        sample = filter_kinetic_sample(sample, filter_indexes)

    methods = get_optimization_methods()
    raw_results = []
    successful_models = []

    for model_config in request_json['models']:
        model_id = model_config['model']
        model_data = find_kinetic_model(model_id)
        kinetic_model = KineticNoLinearModel(model_data)
        try:
            fit_results = kinetic_model.run(
                sample=sample,
                seeds=model_config['seeds'],
                methods=methods,
                step=model_config.get('step'),
                iterations=model_config.get('iterations'),
            )
            raw_results.append({
                "model": model_id,
                "adjustments": fit_results,
                "best_adjust": kinetic_model.get_best_method_name(),
                "seeds": model_config['seeds'],
            })
            successful_models.append((kinetic_model, model_id))
        except Exception as e:
            raw_results.append({"model": model_id, "error": str(e)})

    comparison = get_kinetic_comparison(successful_models, sample)

    formatted_results = [
        {
            "adjustment_methods": [
                ResponseFormatter.format_fit_result(fr)
                for fr in r["adjustments"]
            ],
            "best_adjust": r["best_adjust"],
            "model": r["model"],
            "seeds": r["seeds"],
        }
        for r in raw_results
        if "error" not in r
    ]

    return formatted_results, comparison
