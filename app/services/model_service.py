import logging

from database import Model, Linearization
from entities.schemas.linearization_schema import LINEARIZATION_SCHEMA
from entities.schemas.model_schema import MODEL_SCHEMA
from exceptions.exceptions import NotFoundError
from services.sample_service import find_sample
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


def excecute_linearizations(investigation, linearizations, model_id):
    model = find_model(model_id)
    result = {"model": model.name}
    sample = find_sample(investigation.sample_id)

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


def process_model(model_id, sample, seeds):
    model = find_model(model_id)
    return model.run(sample, seeds)


def exec_no_linear_models(investigation, seeds, model_id):
    result = {"model": model_id}
    sample = find_sample(investigation.sample_id)

    adjustments = process_model(model_id, sample, seeds)
    formated_adjustments = []
    for adjustment in adjustments:
        formated_solution = format_solution_no_linear(**adjustment)
        formated_adjustments.append(formated_solution)

    result["adjustment_methods"] = formated_adjustments
    return result

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