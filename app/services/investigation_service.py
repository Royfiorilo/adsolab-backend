from datetime import datetime

from marshmallow import ValidationError

from app import db
from database import Investigation
from entities.schemas.investigation_schema import INVESTIGATION_SCHEMA
from exceptions.exceptions import BadRequestError, LinearizationError, NotFoundError
from services.comparison_service import get_comparison
from services.linearization_service import execute_linearizations
from services.no_linear_model_service import process_models, format_results
from services.sample_service import create_sample_db, find_sample, filter_sample
from services.version_service import create_version, save_version, validate_and_get_version, get_versions_by_investigation


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
    investigation = Investigation.with_schema(INVESTIGATION_SCHEMA).filter_by(investigation_id=investigation_id).first()
    if investigation is None:
        raise NotFoundError(f"Investigation with ID {investigation_id} not found")
    return investigation


def get_investigations_from_db():
    investigations = Investigation.with_schema(INVESTIGATION_SCHEMA).all()
    return investigations


def run_linearization_models(request_data):
    results = []
    investigation = get_investigation(request_data['investigation_id'])

    filter = request_data['filter'] if 'filter' in request_data.keys() else None

    for model in request_data["models"]:
        try:
            model_result = execute_linearizations(investigation, model.get('linearizations', []), model["model"],
                                                  filter)
            results.append(model_result)
        except LinearizationError as e:
            results.append({"model": model["model"], "error": str(e)})

    return results


def run_no_linear_models(request_data):
    investigation = get_investigation(request_data['investigation_id'])
    filter_params = request_data.get('filter')

    results, models = process_models(
        investigation,
        request_data["models"],
        filter_params
    )

    # Sample data and filter
    sample = find_sample(investigation.sample_id)
    filter_sample(sample, filter_params)

    # comparison
    print(f"Executing comparison: {datetime.now()}")
    comparison = get_comparison(results, models, sample.qe)

    formatted_results = format_results(results)

    return formatted_results, comparison

def is_valid_investigation(investigation_id):
    return Investigation.with_schema(None).filter_by(investigation_id=investigation_id).count() > 0

def validate_and_save_version(request_json):
    if not is_valid_investigation(request_json["investigation_id"]):
        raise NotFoundError(f"Investigation with ID {request_json['investigation_id']} not found")
    version_data = create_version(request_json)
    version = save_version(version_data)
    return version

def get_version(investigation_id, version_id):
    investigation = get_investigation(investigation_id)
    version = validate_and_get_version(version_id, investigation)
    return version


def get_versions(request_json):
    investigation = get_investigation(request_json['investigation_id'])
    versions = get_versions_by_investigation(investigation.id)
    return versions


def delete_investigation(investigation_id):
    if not is_valid_investigation(investigation_id):
        raise NotFoundError(f"Investigation with ID {investigation_id} not found")

    investigation = db.session.query(Investigation).filter_by(investigation_id=investigation_id).first()
    db.session.delete(investigation)
    db.session.commit()

