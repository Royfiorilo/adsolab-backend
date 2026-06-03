"""
kinetics_linearization_service.py

Responsabilidad:
    Ejecutar las linealizaciones de modelos cinéticos cuando estén definidas.

    Equivalente a `linearization_service.py` del módulo de equilibrio, pero
    usando `time` / `qt` como variables en lugar de `ce` / `qe`.

    Este servicio es opcional en el primer alcance del módulo cinético;
    puede implementarse en una iteración posterior si Jorge/Silvia confirman
    que se requieren linealizaciones cinéticas (e.g. ln(qe - qt) vs t para PFO,
    t/qt vs t para PSO).

    TODO: implementar una vez que las linealizaciones cinéticas sean validadas.
"""
from scipy.stats import linregress
from sympy import Eq, solve, sympify, symbols, diff
import numpy as np

from entities.formula import Formula
from utils import round_number, round_list_numbers

ROUND_DIGIT = 4


def _transform_points(sample, x_formula: Formula, y_formula: Formula):
    x_dots, y_dots = [], []
    for t, q in zip(sample.time, sample.qt):
        data = {"time": float(t), "qt": float(q)}
        x_dots.append(round(float(x_formula.apply(**data)), ROUND_DIGIT))
        y_dots.append(round(float(y_formula.apply(**data)), ROUND_DIGIT))
    return x_dots, y_dots


def _solve_params(equations: dict, result_lr) -> tuple:
    eq_m = Eq(sympify(equations['m'], evaluate=False), result_lr.slope)
    eq_b = Eq(sympify(equations['b'], evaluate=False), result_lr.intercept)

    all_syms = eq_m.free_symbols | eq_b.free_symbols
    unknowns = tuple(all_syms)
    solutions = solve((eq_m, eq_b), unknowns)

    if isinstance(solutions, dict):
        params_values = {str(k): float(v) for k, v in solutions.items()}
    elif isinstance(solutions, list) and solutions:
        first = solutions[0]
        params_values = {str(unknowns[i]): float(first[i]) for i in range(len(unknowns))}
    else:
        params_values = {str(unknowns[i]): float(v) for i, v in enumerate(solutions)}

    cov_matrix = np.array([
        [result_lr.stderr ** 2, 0],
        [0, result_lr.intercept_stderr ** 2]
    ])

    params_stderr = {}
    for sym_name in params_values:
        sym = symbols(sym_name)
        df_dm = float(diff(sympify(equations['m']), sym).subs(
            {symbols(k): v for k, v in params_values.items()}
        ))
        df_db = float(diff(sympify(equations['b']), sym).subs(
            {symbols(k): v for k, v in params_values.items()}
        ))
        derivatives = np.array([df_dm, df_db])
        params_stderr[sym_name] = float(np.sqrt(np.dot(derivatives, np.dot(cov_matrix, derivatives))))

    return params_values, params_stderr


def _run_single_linearization(sample, lin_data: dict) -> dict:
    parameters = lin_data.get('parameters', {})
    x_formula = Formula(parameters['x'])
    y_formula = Formula(parameters['y'])

    x_dots, y_dots = _transform_points(sample, x_formula, y_formula)

    try:
        result_lr = linregress(x_dots, y_dots)
    except ValueError as e:
        return {"name": lin_data['name'], "id": lin_data['linearization_id'], "status": "ERROR", "reason": str(e)}

    equations = {k: v for k, v in parameters.items() if k not in ('x', 'y')}
    params_values, params_stderr = _solve_params(equations, result_lr)

    return {
        "name": lin_data['name'],
        "id": lin_data['linearization_id'],
        "status": "OK",
        "transformed": {"x": x_dots, "y": round_list_numbers(y_dots)},
        "slope": round_number(result_lr.slope),
        "intercept": round_number(result_lr.intercept),
        "statistics": {"r_squared": round(result_lr.rvalue ** 2, ROUND_DIGIT)},
        "parameters": [
            {
                "name": name,
                "value": round_number(value),
                "std_err": round_number(params_stderr.get(name)),
            }
            for name, value in params_values.items()
        ],
    }


def run_kinetic_linearization(request_json: dict):
    """
    Ejecuta linealizaciones para los modelos cinéticos solicitados.

    Flujo equivalente a `run_linearization_models` de `investigation_service.py`:
      1. Recuperar muestra cinética.
      2. Para cada modelo y linealización definida: transformar datos (time, qt).
      3. Ajustar regresión lineal con scipy.stats.linregress.
      4. Resolver sistema de ecuaciones con SymPy para recuperar parámetros.
      5. Propagar incertidumbres mediante Jacobiano.

    TODO: implementar.
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

        linearization_results = []
        best_result = None

        for lin_id in linearization_ids:
            lin_db = db.session.query(KineticLinearization).filter_by(
                linearization_id=lin_id
            ).first()
            if lin_db is None:
                continue

            lin_data = KINETICS_LINEARIZATION_SCHEMA.dump(lin_db)
            result = _run_single_linearization(sample, lin_data)
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
