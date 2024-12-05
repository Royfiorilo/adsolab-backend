from marshmallow import ValidationError

from app import db
from database import Investigation
from entities.schemas.investigation_schema import INVESTIGATION_SCHEMA
from exceptions.exceptions import BadRequestError, LinearizationError, NotFoundError
from services.model_service import excecute_linearizations, exec_no_linear_models, get_best_model
from services.sample_service import create_sample_db, find_sample


def create_investigation_and_sample(request_json):
    sample = create_sample_db(request_json)
    investigation = _create_investigation_db(sample.sample_id)

    return investigation


def create_investigation_with_sample_id(sample_id):
    sample = find_sample(sample_id)
    investigation = _create_investigation_db(sample.sample_id)
    return investigation


def _create_investigation_db(sample_id):
    try:
        investigation = Investigation(sample_id=sample_id)
        db.session.add(investigation)
        db.session.commit()

        result = INVESTIGATION_SCHEMA.dump(investigation)
        return result
    except ValidationError as me:
        db.session.rollback()
        raise BadRequestError(f"Validation Error: {me}")


def get_investigation(investigation_id):
    investigation = Investigation.with_schema(None).filter_by(investigation_id=investigation_id).first()
    if investigation is None:
        raise NotFoundError(f"Investigation with ID {investigation_id} not found")
    return investigation


def run_linearization_models(request_data):
    results = []
    investigation = get_investigation(request_data['investigation_id'])

    for model in request_data["models"]:
        try:
            model_result = execute_model_linearization(investigation, model)
            results.append(model_result)
        except LinearizationError as e:
            results.append({"model": model["model"], "error": str(e)})

    return results


def execute_model_linearization(investigation, model):
    return excecute_linearizations(
        investigation,
        model.get('linearizations', []),
        model["model"]
    )



def  run_no_linear_models(request_data):
    results = []

    investigation = get_investigation(request_data['investigation_id'])

    for model in request_data["models"]:
        try:
            model_result, model = exec_no_linear_models(investigation, model.get("seeds"), model["model"])
            results.append(model_result)

        except LinearizationError as e:
            results.append({"model": model["model"], "error": str(e)})

    best_model = get_best_model(results, model)

    return results, best_model
