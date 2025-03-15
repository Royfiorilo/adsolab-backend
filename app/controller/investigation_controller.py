from datetime import datetime
from http import HTTPStatus

from flask import Blueprint, request, jsonify
from flask_security import auth_required
from flask_login import current_user

from entities.schemas.investigation_schema import INVESTIGATION_SCHEMA
from exceptions.exceptions import BadRequestError
from services.investigation_service import run_linearization_models, run_no_linear_models, create_investigation_with_sample_id, \
    get_investigations_from_db, validate_and_save_version, get_version, get_versions_by_investigation, \
    delete_investigation, predict_models_seeds
from services.version_service import delete_investigation_version

blueprint = Blueprint('investigation', __name__)

@blueprint.route('/investigation/run-linearization', methods=['POST'])
def execute_linear_models():
    request_json = request.get_json()

    if "sample_id" not in request_json or "models" not in request_json:
        raise BadRequestError("sample_id and models are required")

    results = run_linearization_models(request_json)
    response = {
        "sample_id": request_json['sample_id'],
        "results": results
    }
    return jsonify(response), HTTPStatus.OK

@blueprint.route('/investigation/run-no-linear-model', methods=['POST'])
def execute_no_linear_models():
    request_json = request.get_json()

    if "sample_id" not in request_json or "models" not in request_json:
        raise BadRequestError("sample_id and models are required")

    print(f"Arranco a comparar:{datetime.now()}")
    results, comparision = run_no_linear_models(request_json)
    print(f"Finaliza la comparacion:{datetime.now()}")
    response = {
        "sample_id": request_json['sample_id'],
        "results": results,
        "comparison": comparision
    }
    return jsonify(response), HTTPStatus.OK

@blueprint.route('/investigation/predict-seeds', methods=['POST'])
def predict_seeds():
    request_json = request.get_json()
    if "sample_id" not in request_json or "models" not in request_json:
        raise BadRequestError("sample_id and models are required")

    results = predict_models_seeds(request_json)
    response = {
        "sample_id": request_json['sample_id'],
        "results": results
    }
    return jsonify(response), HTTPStatus.OK

@blueprint.route('/investigations', methods=['GET'])
def get_investigations():
    investigations_db = get_investigations_from_db()

    investigations = []
    for investigation in investigations_db:
        investigations.append(INVESTIGATION_SCHEMA.dump(investigation))


    response =  {"investigations": investigations}

    return jsonify(response), HTTPStatus.OK

@blueprint.route('/investigation/save', methods=['POST'])
@auth_required()
def save():
    request_json = request.get_json()
    if "sample_id" not in request_json:
        raise BadRequestError("sample_id is required")
    try:
        if 'investigation_id' not in request_json:
            request_json['user_id'] = current_user.id
            investigation = create_investigation_with_sample_id(request_json)
            request_json['investigation_id'] = investigation['investigation_id']
        version = validate_and_save_version(request_json)
    except Exception as e:
        raise e
    return {"status": "ok", "version_id": version.version_id, "investigation_id": request_json['investigation_id']}, HTTPStatus.CREATED


@blueprint.route('/investigation/<int:investigation_id>/version/<int:version_id>', methods=['GET'])
def get_investigation_version(investigation_id, version_id):
    try:
        version = get_version(investigation_id, version_id)
    except Exception as e:
        raise e
    return jsonify(version), HTTPStatus.OK

@blueprint.route('/investigation/<int:investigation_id>/versions', methods=['GET'])
def get_investigation_versions(investigation_id):
    try:
        versions = get_versions_by_investigation(investigation_id)
    except Exception as e:
        raise e
    response = {
        "investigation_id": investigation_id,
        "versions": versions
    }
    return response, HTTPStatus.OK

@blueprint.route('/investigation/<int:investigation_id>/version/<int:version_id>', methods=['DELETE'])
def delete_version(investigation_id, version_id):
    try:
        delete_investigation_version(investigation_id, version_id)
    except Exception as e:
        raise e
    response = {
        "investigation_id": investigation_id,
        "version_id": version_id
    }
    return response, HTTPStatus.OK

@blueprint.route('/investigation/<int:investigation_id>', methods=['DELETE'])
def delete(investigation_id):
    try:
        delete_investigation(investigation_id)
    except Exception as e:
        raise e
    response = {
        "investigation_id": investigation_id
    }
    return response, HTTPStatus.OK

