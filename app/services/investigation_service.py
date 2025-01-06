from marshmallow import ValidationError

from app import db
from database import Investigation
from entities.schemas.investigation_schema import INVESTIGATION_SCHEMA
from exceptions.exceptions import BadRequestError, LinearizationError, NotFoundError
from services.model_service import excecute_linearizations, exec_no_linear_models, get_comparision
from services.sample_service import create_sample_db, find_sample, filter_sample
from utils import  soft_curves_response


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

    filter = request_data['filter'] if 'filter' in request_data.keys() else None

    for model in request_data["models"]:
        try:
            model_result = execute_model_linearization(investigation, model, filter)
            results.append(model_result)
        except LinearizationError as e:
            results.append({"model": model["model"], "error": str(e)})

    return results


def execute_model_linearization(investigation, model, filter):
    return excecute_linearizations(
        investigation,
        model.get('linearizations', []),
        model["model"],
        filter
    )


    
def  run_no_linear_models(request_data):
    results = []
    models = []
    investigation = get_investigation(request_data['investigation_id'])

    filter = request_data['filter'] if 'filter' in request_data.keys() else None

    for model in request_data["models"]:
        try:
            model_result, model = exec_no_linear_models(investigation, model, filter)
            results.append(model_result)
            models.append(model)
        except LinearizationError as e:
            results.append({"model": model["model"], "error": str(e)})


    sample = find_sample(investigation.sample_id)
    filter_sample(sample, filter)

    comparision = get_comparision(results, models, sample.qe)

    soft_curves_response(results, comparision,sample.ce)
    return results, comparision
