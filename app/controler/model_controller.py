from http import HTTPStatus

from flask import jsonify, Blueprint
from entities.schemas.model_schema import MODEL_SCHEMA


blueprint = Blueprint('model', __name__)


@blueprint.route('/models', methods=['GET'])
def get_models():
    models = get_models()
    output = []

    for model in models:
        model_json = MODEL_SCHEMA.dump(model)
        output.append(model_json)

    response = {'models': output}
    return jsonify(response), HTTPStatus.OK
