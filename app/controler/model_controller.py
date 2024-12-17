from http import HTTPStatus

from flask import jsonify, Blueprint
from entities.schemas.model_schema import MODEL_SCHEMA
from entities.schemas.method_schema import METHOD_SCHEMA
from services.model_service import find_models, find_methods

blueprint = Blueprint('model', __name__)


@blueprint.route('/models', methods=['GET'])
def get_models():
    models = find_models()
    output = []

    for model in models:
        model_json = MODEL_SCHEMA.dump(model)
        output.append(model_json)

    response = {'models': output}
    return jsonify(response), HTTPStatus.OK


@blueprint.route('/models/methods', methods=['GET'])
def get_adjust_methods():
    methods = find_methods()
    output = []

    for method in methods:
        method_json = METHOD_SCHEMA.dump(method)
        output.append(method_json)

    response = {'methods': output}
    return jsonify(response), HTTPStatus.OK
