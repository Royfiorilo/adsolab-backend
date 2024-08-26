from http import HTTPStatus

from flask import jsonify, Blueprint

from database import Model
from entities.schemas.model_schema import MODEL_SCHEMA

blueprint = Blueprint('model', __name__)



@blueprint.route('/models', methods=['GET'])
def get_models():
    models = Model.with_schema(None).all()

    if not models:
        return jsonify({"status": "error", "message": "No models found"}), HTTPStatus.NOT_FOUND

    output = []

    for model in models:
        model_json = MODEL_SCHEMA.dump(model)
        output.append(model_json)

    response = {'models': output}
    return jsonify(response), HTTPStatus.OK
