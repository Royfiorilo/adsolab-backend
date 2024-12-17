import logging
from typing import Dict
import numpy as np

from database import Model, Linearization, Method
from entities.comparator import AdsorptionModelComparison
from entities.schemas.linearization_schema import LINEARIZATION_SCHEMA
from entities.schemas.model_schema import MODEL_SCHEMA
from exceptions.exceptions import NotFoundError
from services.sample_service import find_sample, filter_sample
from utils import round_list_numbers, round_number


def find_models():
    models  = Model.with_schema(None).all()
    if not models:
        raise NotFoundError('No models found')
    return models


def find_model(model_id):
    model = Model.with_schema(MODEL_SCHEMA).filter_by(_id=model_id).first()
    if not model:
        raise NotFoundError(f'Model {model_id} not found')
    return model


def compare_r2_linearizations(linearization1, linearization2):
    if not linearization1:
        return linearization2

    return linearization1 if abs(linearization1["statistics"]["r_squared"]) >= abs(
        linearization2["statistics"]["r_squared"]) else linearization2


def excecute_linearizations(investigation, linearizations, model_id, filter: None):
    model = find_model(model_id)
    result = {"model": model.name}
    sample = find_sample(investigation.sample_id)

    filter_sample(sample,filter)

    linearization_results = []
    best_result = None

    for linearization_id in linearizations:
        solution = process_linearization(linearization_id, sample)
        formated_solution = format_solution_linearization(**solution)
        linearization_results.append(formated_solution)

        if formated_solution["status"] == "OK":
            best_result = compare_r2_linearizations(best_result, formated_solution)
            result["best_result"] = best_result["id"]

    result["linearizations"] = linearization_results
    return result


def process_linearization(linearization_id, sample):
    linearization = Linearization.with_schema(LINEARIZATION_SCHEMA).filter_by(linearization_id=linearization_id).first()
    if linearization is None:
        me = f"Linearization '{linearization_id}' not found"
        logging.error(me)
        raise NotFoundError(me)

    return linearization.run(sample)


def process_model(model_name, sample, seeds, methods):
    model = find_model(model_name)
    return model.run(sample, seeds, methods), model


def exec_no_linear_models(investigation, seeds, model_name, filter: None):
    methods = get_optimization_methods()
    sample = find_sample(investigation.sample_id)

    filter_sample(sample,filter)

    adjustments, model  = process_model(model_name, sample, seeds, methods)
    adjustments["model"] = model_name

    return adjustments, model


def get_comparision(results, models, y):
    compare = []
    y_preds = []
    model_results_ridge = []


    for idx, result in enumerate(results):
        best_method = models[idx].get_best_method()
        compare.append({"statistics": best_method["statistics"], "name": result["model"], "residuals": best_method["residuals"]})
        y_preds.append(best_method['transformed']['y'])

    scores_heuristic = AdsorptionModelComparison.determine_heuristic_scores_models(compare, "name")
    best_model_heuristic = max(scores_heuristic, key=scores_heuristic.get)

    score_ridge = AdsorptionModelComparison.get_ml_coefs_models(y, y_preds)
    coefs = score_ridge['coefs']

    for idx, model in enumerate(models):
        model_results_ridge.append({
            'model': model._id,
            'coef': coefs[idx]
        })


    max_model_ridge = max(coefs)
    best_model_ridge = coefs.index(max_model_ridge)
    best_model_ridge = model_results_ridge[best_model_ridge]['model']
    comparision = format_comparision(scores_heuristic, best_model_heuristic, score_ridge, best_model_ridge, model_results_ridge)

    return comparision


def format_comparision(scores_heuristic, best_heuristic, score_ridge, best_ridge, model_results_ridge):
    return {
        "heuristic": {
            "best_model": best_heuristic,
            "results": [{'model': model, 'score': round_number(score)} for model, score in scores_heuristic.items()]
        },
        "ridge": {
            "best_model": best_ridge,
            "y_pred": score_ridge['y_pred'],
            "statistics":score_ridge['statistics'],
            "results": model_results_ridge
        }
    }

def format_solution_linearization(name, id, x, y, slope, intercept, vars, params_info, statistics):
    parameters = []
    for var in vars:
        parameters.append(
            {"name": var,
             "value": round_number(params_info[0][var]),
             "stderr": round_number(params_info[1][var])
             })

    return {
        "name": name,
        "id": id,
        "status": "OK",
        "transformed": {"x": x, "y": round_list_numbers(y)},
        "slope": slope,
        "intercept": intercept,
        "statistics": statistics,
        "parameters": parameters
    }


def format_solution_no_linear(name, description, success, vars,params, x, y_pred, stats):
    parameters = []
    for var in vars:
        parameters.append(
            {"name": var,
             "value": round_number(params[0][var]),
             "stderr": round_number(params[1][var]) if params[1][var] is not None else None
             })

    return {
        "name": name,
        "description": description,
        "status": success,
        "transformed": {"x": x, "y": round_list_numbers(y_pred)},
        "statistics": stats,
        "parameters": parameters
    }



def get_optimization_methods() -> Dict[str, str]:
    methods = find_methods()
    method_dict = {}

    for method in methods:
        method_dict[method.code] = method.description

    return method_dict

def find_methods():
    methods = Method.with_schema(None).all()
    if not methods:
        raise NotFoundError('No adjust methods found')
    return methods

