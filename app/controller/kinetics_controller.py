from http import HTTPStatus
from datetime import datetime

from flask import Blueprint, request, jsonify
from flask_security import auth_required
from flask_login import current_user

from entities.schemas.kinetics_sample_schema import KINETICS_SAMPLE_SCHEMA
from entities.schemas.kinetics_investigation_schema import KINETICS_INVESTIGATION_SCHEMA
from entities.schemas.kinetics_historic_schema import KINETICS_VERSION_SCHEMA
from exceptions.exceptions import BadRequestError
from services.kinetics_model_service import find_kinetic_models
from services.kinetics_sample_service import (
    get_all_kinetic_samples, find_kinetic_sample,
    create_kinetic_sample_db, delete_kinetic_sample,
)
from services.kinetics_investigation_service import (
    run_kinetics_predict_seeds, run_kinetics_no_linear,
    get_kinetic_investigations, validate_and_save_kinetic_version,
    delete_kinetic_investigation,
)
from services.kinetics_version_service import (
    get_kinetic_version, get_kinetic_versions, delete_kinetic_version,
)
from services.kinetics_linearization_service import run_kinetic_linearization

blueprint = Blueprint('kinetics', __name__)


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

@blueprint.route('/kinetics/models', methods=['GET'])
def get_kinetic_models():
    """Lista todos los modelos cinéticos disponibles."""
    models = find_kinetic_models()
    return jsonify({"models": models}), HTTPStatus.OK


# ---------------------------------------------------------------------------
# Samples
# ---------------------------------------------------------------------------

@blueprint.route('/kinetics/samples', methods=['GET'])
def get_kinetics_samples():
    """Lista muestras cinéticas activas."""
    samples = get_all_kinetic_samples()
    output = [KINETICS_SAMPLE_SCHEMA.dump(s) for s in samples]
    return jsonify({"samples": output}), HTTPStatus.OK


@blueprint.route('/kinetics/sample/<int:kinetic_sample_id>', methods=['GET'])
def get_kinetics_sample_by_id(kinetic_sample_id):
    """Recupera una muestra cinética por ID."""
    sample = find_kinetic_sample(kinetic_sample_id)
    return jsonify(KINETICS_SAMPLE_SCHEMA.dump(sample)), HTTPStatus.OK


@blueprint.route('/kinetics/sample', methods=['POST'])
@auth_required()
def create_kinetics_sample():
    """Crea una muestra cinética nueva y la asocia al usuario autenticado."""
    request_json = request.get_json()
    request_json['user_id'] = current_user.id
    sample = create_kinetic_sample_db(request_json)
    return jsonify(KINETICS_SAMPLE_SCHEMA.dump(sample)), HTTPStatus.CREATED


@blueprint.route('/kinetics/sample/<int:kinetic_sample_id>', methods=['DELETE'])
@auth_required()
def delete_kinetics_sample(kinetic_sample_id):
    """Soft-delete de una muestra cinética."""
    delete_kinetic_sample(kinetic_sample_id, current_user.id)
    return jsonify({"kinetic_sample_id": kinetic_sample_id}), HTTPStatus.OK


# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------

@blueprint.route('/kinetics/predict-seeds', methods=['POST'])
def predict_seeds():
    """Estima parámetros iniciales (seeds) para los modelos cinéticos solicitados."""
    request_json = request.get_json()
    if 'kinetic_sample_id' not in request_json or 'models' not in request_json:
        raise BadRequestError("kinetic_sample_id and models are required.")

    results = run_kinetics_predict_seeds(request_json)
    return jsonify({
        "kinetic_sample_id": request_json['kinetic_sample_id'],
        "results": results,
    }), HTTPStatus.OK


@blueprint.route('/kinetics/run-linearization', methods=['POST'])
def execute_kinetic_linearization():
    """Ejecuta linealizaciones cinéticas (opcional, iteración futura)."""
    request_json = request.get_json()
    if 'kinetic_sample_id' not in request_json or 'models' not in request_json:
        raise BadRequestError("kinetic_sample_id and models are required.")

    results = run_kinetic_linearization(request_json)
    return jsonify({
        "kinetic_sample_id": request_json['kinetic_sample_id'],
        "results": results,
    }), HTTPStatus.OK


@blueprint.route('/kinetics/run-no-linear-model', methods=['POST'])
def execute_kinetic_no_linear_models():
    """Ejecuta el ajuste no lineal de modelos cinéticos y devuelve resultados + comparación."""
    request_json = request.get_json()
    if 'kinetic_sample_id' not in request_json or 'models' not in request_json:
        raise BadRequestError("kinetic_sample_id and models are required.")

    print(f"[kinetics] Inicio ajuste no lineal: {datetime.now()}")
    results, comparison = run_kinetics_no_linear(request_json)
    print(f"[kinetics] Fin ajuste no lineal: {datetime.now()}")

    return jsonify({
        "kinetic_sample_id": request_json['kinetic_sample_id'],
        "results": results,
        "comparison": comparison,
    }), HTTPStatus.OK


# ---------------------------------------------------------------------------
# Investigations & Versions (historic)
# ---------------------------------------------------------------------------

@blueprint.route('/kinetics/investigations', methods=['GET'])
def get_kinetics_investigations():
    """Lista investigaciones cinéticas paginadas."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    user_id = request.args.get('user_id', None, type=int)

    result = get_kinetic_investigations(page, per_page, user_id)
    result['investigations'] = [
        KINETICS_INVESTIGATION_SCHEMA.dump(i) for i in result['investigations']
    ]
    return jsonify(result), HTTPStatus.OK


@blueprint.route('/kinetics/investigation/save', methods=['POST'])
@auth_required()
def save_kinetics_investigation():
    """Crea o actualiza una investigación cinética con una nueva versión de resultados."""
    request_json = request.get_json()
    response = validate_and_save_kinetic_version(request_json, current_user.id)
    return jsonify(response), HTTPStatus.CREATED


@blueprint.route(
    '/kinetics/investigation/<int:kinetic_investigation_id>/versions', methods=['GET']
)
def get_kinetics_versions(kinetic_investigation_id):
    """Lista las versiones guardadas de una investigación cinética."""
    versions = get_kinetic_versions(kinetic_investigation_id)
    return jsonify({
        "versions": [KINETICS_VERSION_SCHEMA.dump(v) for v in versions]
    }), HTTPStatus.OK


@blueprint.route(
    '/kinetics/investigation/<int:kinetic_investigation_id>/version/<int:version_id>',
    methods=['GET']
)
def get_kinetics_version(kinetic_investigation_id, version_id):
    """Recupera una versión específica de una investigación cinética."""
    version = get_kinetic_version(kinetic_investigation_id, version_id)
    return jsonify(KINETICS_VERSION_SCHEMA.dump(version)), HTTPStatus.OK


@blueprint.route(
    '/kinetics/investigation/<int:kinetic_investigation_id>/version/<int:version_id>',
    methods=['DELETE']
)
@auth_required()
def delete_kinetics_version(kinetic_investigation_id, version_id):
    """Elimina una versión de investigación cinética."""
    delete_kinetic_version(kinetic_investigation_id, version_id, current_user.id)
    return jsonify({
        "kinetic_investigation_id": kinetic_investigation_id,
        "version_id": version_id,
    }), HTTPStatus.OK


@blueprint.route(
    '/kinetics/investigation/<int:kinetic_investigation_id>', methods=['DELETE']
)
@auth_required()
def delete_kinetics_investigation(kinetic_investigation_id):
    """Elimina una investigación cinética completa con todas sus versiones."""
    delete_kinetic_investigation(kinetic_investigation_id, current_user.id)
    return jsonify({
        "kinetic_investigation_id": kinetic_investigation_id
    }), HTTPStatus.OK
