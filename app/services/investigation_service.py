from datetime import datetime

from marshmallow import ValidationError
from sqlalchemy import exists

from app import db
from database import Investigation, Version
from entities.schemas.investigation_schema import INVESTIGATION_SCHEMA
from exceptions.exceptions import BadRequestError, LinearizationError, NotFoundError, ForbiddenError
from services.comparison_service import get_comparison
from services.linearization_service import execute_linearizations
from services.no_linear_model_service import process_models, format_results, calculate_predicted_seeds
from services.sample_service import find_sample, filter_sample
from services.version_service import create_version, save_version, validate_and_get_version, \
    get_versions_by_investigation


def create_investigation_with_sample_id(request_json):
    sample_id = request_json['sample_id']
    user_id = request_json['user_id']
    sample = find_sample(sample_id)
    investigation = _create_investigation_db(sample.sample_id, user_id)
    return investigation


def _create_investigation_db(sample_id, user_id):
    try:
        investigation = Investigation(sample_id=sample_id, user_id=user_id)
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


def get_investigations_from_db(page, per_page, user_id):
    per_page = min(per_page, 100)
    offset = (page - 1) * per_page
    if user_id:
        total = Investigation.with_schema(INVESTIGATION_SCHEMA).filter_by(user_id=user_id).filter(
            exists().where(Version.investigation_id == Investigation.investigation_id)).count()
        investigations = Investigation.with_schema(INVESTIGATION_SCHEMA).filter_by(user_id=user_id).filter(
            exists().where(Version.investigation_id == Investigation.investigation_id)).limit(per_page).offset(
            offset).all()
    else:
        total = Investigation.with_schema(INVESTIGATION_SCHEMA).filter(
            exists().where(Version.investigation_id == Investigation.investigation_id)).count()
        investigations = Investigation.with_schema(INVESTIGATION_SCHEMA).filter(
            exists().where(Version.investigation_id == Investigation.investigation_id)).limit(per_page).offset(
            offset).all()

    return {"investigations": investigations,
            'page': page,
            'per_page': per_page,
            'total': total,
            'pages': (total // per_page) + (1 if total % per_page > 0 else 0)}


def run_linearization_models(request_data):
    results = []

    filter = request_data['filter'] if 'filter' in request_data.keys() else None

    # Sample data and filter
    sample = find_sample(request_data['sample_id'])
    filter_sample(sample, filter)

    for model in request_data["models"]:
        try:
            model_result = execute_linearizations(sample, model.get('linearizations', []), model["model"])
            results.append(model_result)
        except LinearizationError as e:
            results.append({"model": model["model"], "error": str(e)})

    return results


def predict_models_seeds(request_data):
    results = []

    filter = request_data['filter'] if 'filter' in request_data.keys() else None

    # Sample data and filter
    sample = find_sample(request_data['sample_id'])
    filter_sample(sample, filter)

    for model in request_data["models"]:
        try:
            if not model.get('linearizations'):
                model_result = calculate_predicted_seeds(sample, model["model"])
                results.append(model_result)
        except LinearizationError as e:
            results.append({"model": model["model"], "error": str(e)})

    return results


def run_no_linear_models(request_data):
    filter_params = request_data.get('filter')

    # Sample data and filter
    sample = find_sample(request_data['sample_id'])
    filter_sample(sample, filter_params)

    results, models = process_models(
        sample,
        request_data["models"]
    )

    # comparison
    print(f"Executing comparison: {datetime.now()}")
    comparison = get_comparison(results, models, sample)

    formatted_results = format_results(results)

    return formatted_results, comparison


def is_valid_investigation(investigation_id, user_id):
    investigation = Investigation.with_schema(None).filter_by(investigation_id=investigation_id).first()
    if not investigation:
        raise NotFoundError(f"Investigation with ID {investigation_id} not found")

    if investigation.user_id != user_id:
        raise ForbiddenError(f"User is not authorized to modify this investigation")


def validate_and_save_version(request_json):
    try:
        is_valid_investigation(request_json["investigation_id"], request_json["user_id"])
    except (NotFoundError, ForbiddenError, BadRequestError):
        raise
    version_data = create_version(request_json)
    version = save_version(version_data)
    return version


def get_version(investigation_id, version_id):
    investigation = get_investigation(investigation_id)
    version = validate_and_get_version(version_id, investigation)
    return version


def get_versions(investigation_id):
    investigation = get_investigation(investigation_id)
    versions = get_versions_by_investigation(investigation.id)
    return versions


def delete_investigation(investigation_id, user_id):
    try:
        is_valid_investigation(investigation_id, user_id)
    except (NotFoundError, ForbiddenError, BadRequestError):
        raise
    investigation = db.session.query(Investigation).filter_by(investigation_id=investigation_id).first()
    db.session.delete(investigation)
    db.session.commit()
