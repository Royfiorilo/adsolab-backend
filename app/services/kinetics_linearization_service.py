"""
kinetics_linearization_service.py

Responsabilidad:
    Ejecutar las linealizaciones de modelos cinéticos usando `time` / `qt` como
    variables, en lugar de `ce` / `qe` como el módulo de equilibrio.

    Diferencias con `linearization_service.py`:
      - Algunas linealizaciones cinéticas necesitan parámetros que no son datos
        medidos. La de PFO (Lagergren) transforma `y = ln(qe - qt)`, donde `qe`
        es justamente uno de los parámetros a despejar. Esos parámetros se
        resuelven en `_resolve_known_params`: se toman del request si vienen, y
        si no se estiman desde la muestra.
      - Los puntos que no se pueden transformar se descartan en lugar de
        sustituirse por el valor crudo (`linearization.py:35-42`). Sustituir
        inyecta un punto falso: sobre datos PSO sintéticos exactos, el (0, 0)
        que genera `t=0` degrada k2 de 0.020 a 0.034.
"""
import math

from scipy.stats import linregress
from sympy import Eq, solve, sympify
import numpy as np

from entities.formula import Formula
from entities.kinetic_parameters import STRICTLY_POSITIVE_PARAMS
from entities.linear_fit_errors import line_covariance, propagate_std_errors
from exceptions.exceptions import LinearizationError
from utils import round_list_numbers, round_parameter_value

ROUND_DIGIT = 4
MIN_VALID_POINTS = 2
MEASURED_VARIABLES = ("time", "qt")
DEFAULT_PARAM_ESTIMATORS = {
    "qe": lambda sample: max(sample.qt),
}


def _resolve_known_params(sample, x_formula: Formula, y_formula: Formula, provided: dict = None) -> dict:
    required = {
        variable.name
        for formula in (x_formula, y_formula)
        for variable in formula.get_variables()
    } - set(MEASURED_VARIABLES)

    known = {}
    for name in sorted(required):
        if provided and name in provided:
            known[name] = float(provided[name])
            _check_qe_not_below_max_qt(sample, name, known[name])
        elif name in DEFAULT_PARAM_ESTIMATORS:
            known[name] = float(DEFAULT_PARAM_ESTIMATORS[name](sample))
        else:
            raise LinearizationError(
                f"Parameter '{name}' is needed to transform this linearization "
                f"and has no default estimator. Send it in 'known_params'."
            )
    return known


def _check_qe_not_below_max_qt(sample, name: str, value: float):
    # Tran et al. (2017): a qe below the largest measured qt makes ln(qe - qt) undefined.
    if name == "qe" and value < max(sample.qt):
        raise LinearizationError(
            f"qe = {value:.4g} cannot be lower than the largest measured qt ({max(sample.qt):.4g})."
        )


def _apply_formula(formula: Formula, data: dict):
    try:
        with np.errstate(divide='ignore', invalid='ignore'):
            value = float(formula.apply(**data))
    except (ZeroDivisionError, ValueError, TypeError):
        return None
    return value if math.isfinite(value) else None


def _transform_points(sample, x_formula: Formula, y_formula: Formula, known_params: dict = None):
    x_dots, y_dots, dropped = [], [], 0

    for t, q in zip(sample.time, sample.qt):
        data = {**(known_params or {}), "time": float(t), "qt": float(q)}
        x = _apply_formula(x_formula, data)
        y = _apply_formula(y_formula, data)

        if x is None or y is None:
            dropped += 1
            continue

        x_dots.append(round(x, ROUND_DIGIT))
        y_dots.append(round(y, ROUND_DIGIT))

    if len(x_dots) < MIN_VALID_POINTS:
        raise LinearizationError(
            f"Not enough valid points to linearize: only {len(x_dots)} of "
            f"{sample.len()} could be transformed."
        )

    return x_dots, y_dots, dropped


def _solve_params(equations: dict, result_lr) -> dict:
    eq_m = Eq(sympify(equations['m'], evaluate=False), result_lr.slope)
    eq_b = Eq(sympify(equations['b'], evaluate=False), result_lr.intercept)

    all_syms = eq_m.free_symbols | eq_b.free_symbols
    unknowns = tuple(all_syms)
    # Exact rationals (the default) make SymPy hang on log equations such as Elovich's intercept.
    solutions = solve((eq_m, eq_b), unknowns, rational=False)

    try:
        if isinstance(solutions, dict):
            params_values = {str(k): float(v) for k, v in solutions.items()}
        elif isinstance(solutions, list) and solutions:
            first = solutions[0]
            params_values = {str(unknowns[i]): float(first[i]) for i in range(len(unknowns))}
        else:
            params_values = {str(unknowns[i]): float(v) for i, v in enumerate(solutions)}
    except TypeError:
        raise LinearizationError("The fitted line gives no real solution for the parameters.")

    if not params_values or not all(math.isfinite(v) for v in params_values.values()):
        raise LinearizationError("The fitted line gives no finite solution for the parameters.")

    return params_values


def _check_positive_params(params_values: dict):
    for name, value in params_values.items():
        if name in STRICTLY_POSITIVE_PARAMS and value <= 0:
            raise LinearizationError(
                f"The fitted line gives {name} = {value:.4g}, but it must be positive."
            )


def _run_single_linearization(sample, lin_data: dict, provided_params: dict = None) -> dict:
    identity = {"name": lin_data['name'], "id": lin_data['linearization_id']}
    parameters = lin_data.get('parameters', {})

    try:
        x_formula = Formula(parameters['x'])
        y_formula = Formula(parameters['y'])
        known_params = _resolve_known_params(sample, x_formula, y_formula, provided_params)
        x_dots, y_dots, dropped = _transform_points(sample, x_formula, y_formula, known_params)
        result_lr = linregress(x_dots, y_dots)
        equations = {k: v for k, v in parameters.items() if k not in ('x', 'y')}
        params_values = _solve_params(equations, result_lr)
        _check_positive_params(params_values)
        params_stderr = propagate_std_errors(
            sympify(equations['m']), sympify(equations['b']), params_values, line_covariance(result_lr, x_dots)
        )
    except (LinearizationError, ValueError, KeyError) as e:
        return {**identity, "status": "ERROR", "reason": str(e)}

    return {
        **identity,
        "status": "OK",
        "transformed": {"x": x_dots, "y": round_list_numbers(y_dots)},
        "slope": round_parameter_value(result_lr.slope),
        "intercept": round_parameter_value(result_lr.intercept),
        "statistics": {"r_squared": round(result_lr.rvalue ** 2, ROUND_DIGIT)},
        "assumed_params": known_params,
        "dropped_points": dropped,
        "parameters": [
            {
                "name": name,
                "value": round_parameter_value(value),
                "std_err": _round_or_none(params_stderr.get(name)),
            }
            for name, value in params_values.items()
        ],
    }


def _round_or_none(value):
    return None if value is None else round_parameter_value(value)


def run_kinetic_linearization(request_json: dict):
    """
    Ejecuta linealizaciones para los modelos cinéticos solicitados.

    Flujo equivalente a `run_linearization_models` de `investigation_service.py`:
      1. Recuperar muestra cinética.
      2. Para cada modelo y linealización definida: transformar datos (time, qt).
      3. Ajustar regresión lineal con scipy.stats.linregress.
      4. Resolver sistema de ecuaciones con SymPy para recuperar parámetros.
      5. Propagar incertidumbres mediante Jacobiano.

    Cada modelo del request acepta un `known_params` opcional con los valores de
    los parámetros que la transformación necesita conocer de antemano (e.g. `qe`
    para PFO). Si no viene, se estima desde la muestra.
    """
    from app import db
    from database import KineticLinearization
    from entities.schemas.kinetics_model_schema import KINETICS_LINEARIZATION_SCHEMA
    from services.kinetics_sample_service import find_kinetic_sample, filter_kinetic_sample

    sample = find_kinetic_sample(request_json['kinetic_sample_id'])
    filter_indexes = request_json.get('filter', [])
    if filter_indexes:
        sample = filter_kinetic_sample(sample, filter_indexes)

    results = []
    for model_request in request_json['models']:
        model_id = model_request['model']
        linearization_ids = model_request.get('linearizations', [])
        provided_params = model_request.get('known_params', {})

        linearization_results = []
        best_result = None

        for lin_id in linearization_ids:
            lin_db = db.session.query(KineticLinearization).filter_by(
                linearization_id=lin_id
            ).first()
            if lin_db is None:
                continue

            lin_data = KINETICS_LINEARIZATION_SCHEMA.dump(lin_db)
            result = _run_single_linearization(sample, lin_data, provided_params)
            linearization_results.append(result)

            if result['status'] == 'OK':
                if best_result is None or abs(result['statistics']['r_squared']) >= abs(best_result['statistics']['r_squared']):
                    best_result = result

        results.append({
            "model": model_id,
            "linearizations": linearization_results,
            "best_result": best_result['id'] if best_result else None,
        })

    return results
