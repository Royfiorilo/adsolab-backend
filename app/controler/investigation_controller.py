import logging
from datetime import datetime
from http import HTTPStatus

from arrow import now
from flask import Blueprint, request, jsonify

from entities.schemas.investigation_schema import INVESTIGATION_SCHEMA
from exceptions.exceptions import BadRequestError, FilterSampleError
from services.investigation_service import run_linearization_models, \
    create_investigation_and_sample, create_investigation_with_sample_id, run_no_linear_models, \
    get_investigations_from_db, validate_and_save_version
from services.sample_service import find_sample
blueprint = Blueprint('investigation', __name__)


@blueprint.route('/investigation', methods=['POST'])
def create_investigation():
    request_json = request.get_json()
    result = create_investigation_and_sample(request_json)

    return jsonify(result), HTTPStatus.CREATED


@blueprint.route('/investigation/sample', methods=['POST'])
def create_investigation_with_sample():
    request_json = request.get_json()

    if 'sample_id' not in request_json:
        raise BadRequestError("sample_id is required")

    sample_id = find_sample(request_json['sample_id']).sample_id
    investigation = create_investigation_with_sample_id(sample_id)

    return jsonify(investigation), HTTPStatus.CREATED


@blueprint.route('/investigation/run-linearization', methods=['POST'])
def execute_linear_models():
    request_json = request.get_json()

    if "investigation_id" not in request_json or "models" not in request_json:
        raise BadRequestError("investigation_id and models are required")

    results = run_linearization_models(request_json)
    response = {
        "investigation_id": request_json['investigation_id'],
        "results": results
    }
    return jsonify(response), HTTPStatus.OK

@blueprint.route('/investigation/run-no-linear-model', methods=['POST'])
def execute_no_linear_models():
    request_json = request.get_json()

    if "investigation_id" not in request_json or "models" not in request_json:
        raise BadRequestError("investigation_id and models are required")

    print(f"Arranco a comparar:{datetime.now()}")
    results, comparision = run_no_linear_models(request_json)
    print(f"Finaliza la comparacion:{datetime.now()}")
    response = {
        "investigation_id": request_json['investigation_id'],
        "results": results,
        "comparison": comparision
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
def save():
    request_json = request.get_json()
    if "investigation_id" not in request_json:
        raise BadRequestError("investigation_id is required")
    try:
        validate_and_save_version(request_json)
    except Exception as e:
        raise e
    return {"status": "ok"}, HTTPStatus.CREATED