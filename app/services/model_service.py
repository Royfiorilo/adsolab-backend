import logging

from database import Model, Linearization
from entities.schemas.linearization_schema import LINEARIZATION_SCHEMA
from entities.schemas.model_schema import MODEL_SCHEMA
from exceptions.exceptions import NotFoundError
from services.sample_service import find_sample


def find_models():
    models  = Model.with_schema(None).all()
    if not models:
        raise NotFoundError('No models found')
    return models

def compare_r2_linearizations(linearization1, linearization2):
    if not linearization1:
        return linearization2

    return linearization1 if abs(linearization1["statistics"]["r"]) >= abs(
        linearization2["statistics"]["r"]) else linearization2


def excecute_linearizations(investigation, linearizations, model):
    result = {"model": model}
    sample = find_sample(investigation.sample_id)

    linearization_results = []
    best_result = None

    for model_name in linearizations:
        solution = process_linearization(model_name, sample)
        linearization_results.append(solution)

        if solution["status"] == "OK":
            best_result = compare_r2_linearizations(best_result, solution)
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
    model = Model.with_schema(MODEL_SCHEMA).filter_by(name=model_name).first()
    if model is None:
        me = f"Model '{model_name}' not found"
        logging.error(me)
        raise NotFoundError(me)
    return model.run(sample, seeds)


def exec_no_linear_models(investigation, seeds, model_name):
    result = {"model": model_name}
    sample = find_sample(investigation.sample_id)

    solution  = process_model(model_name, sample, seeds)
    result["adjustment_methods"] = solution
    return result