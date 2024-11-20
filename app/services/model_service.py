import logging

from database import Model, Linearization
from entities.comparator import AdsorptionModelComparison
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

def find_model(model_name):
    model = Model.with_schema(MODEL_SCHEMA).filter_by(_id=model_name).first()
    if not model:
        raise NotFoundError(f'Model {model_name} not found')
    return model

def compare_r2_linearizations(linearization1, linearization2):
    if not linearization1:
        return linearization2

    return linearization1 if abs(linearization1["statistics"]["r_squared"]) >= abs(
        linearization2["statistics"]["r_squared"]) else linearization2


def excecute_linearizations(investigation, linearizations, model):
    result = {"model": model}
    sample = find_sample(investigation.sample_id)

    linearization_results = []
    best_result = None

    for model_name in linearizations:
        solution = process_linearization(model_name, sample)
        formated_solution = format_solution_linearization(**solution)
        linearization_results.append(formated_solution)

        if formated_solution["status"] == "OK":
            best_result = compare_r2_linearizations(best_result, formated_solution)
            result["best_result"] = best_result["name"]

    result["linearizations"] = linearization_results
    return result


def process_linearization(model_name, sample):
    linearization = Linearization.with_schema(LINEARIZATION_SCHEMA).filter_by(name=model_name).first()
    if linearization is None:
        me = f"Linearization '{model_name}' not found"
        logging.error(me)
        raise NotFoundError(me)

    return linearization.run(sample)


def process_model(model_name, sample,seeds):
    model = find_model(model_name)
    return model.run(sample, seeds), model


def exec_no_linear_models(investigation, seeds, model_name):
    sample = find_sample(investigation.sample_id)

    adjustments, model  = process_model(model_name, sample, seeds)
    adjustments["model"] = model_name

    return adjustments, model

def get_best_model(results, model):
    compare = []
    for result in results:
        best_method = model.get_best_method()
        compare.append({"statistics": best_method["statistics"], "name": result["model"], "residuals": best_method["residuals"]})

    best_model = AdsorptionModelComparison.determine_best_model(compare, "name")
    return best_model


def format_solution_linearization(name, x, y, slope, intercept, vars, solutions_dict, statistics):
    return {
        "name": name,
        "status": "OK",
        "transformed": {"x": x, "y": round_list_numbers(y)},
        "slope": slope,
        "intercept": intercept,
        "statistics": statistics,
        "parameters": [{"name": var, "value": round_number(solutions_dict[0][var])} for var in vars]
    }

def format_solution_no_linear(name, description, success, params, x, y_pred, stats):
    return {
        "name": name,
        "description": description,
        "status": success,
        "transformed": {"x": x, "y": round_list_numbers(y_pred)},
        "statistics": stats,
        "parameters": [{"name": var, "value": round_number(params[var])} for var in params.keys()]
    }