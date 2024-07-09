from flask import jsonify, request, Blueprint
import numpy as np
from http import HTTPStatus
from app.models.models import *
from app.entities.model import Model as ModelEntity
from app.entities.schemas.model_schema import MODEL_SCHEMA
from app.database import Model, Linearization

blueprint = Blueprint('model', __name__)

@blueprint.route('/run-model/<model_name>', methods=['POST'])
def run_model(model_name):
    data = request.get_json()
    dot_x = data['x']
    x = np.array(dot_x)

    modeldb = Model.query.filter_by(name=model_name).first()
    model = ModelEntity(modeldb._id, modeldb.name, modeldb.formula, modeldb.description, modeldb.parameters, modeldb.linearizations)

    if not model:
        return jsonify({"status": "error", "message": "Model not found"}), HTTPStatus.NOT_FOUND

    linearization = Linearization.query.filter_by(model_id=model.id).all()

    match model_name.lower():
        case 'langmuir':
            apply_model = np.vectorize(langmuir)
            y_model = list(apply_model(0.198, 0.189, x))
        case _:
            return jsonify({"status": "error", "message": "Model not implemented"}), HTTPStatus.NOT_FOUND

    response = {
        "x": dot_x,
        "y": y_model,
        "formula": model.formula
    }
    return jsonify(response), HTTPStatus.OK


@blueprint.route('/models', methods=['GET'])
def get_models():
    models = Model.query.all()

    if not models:
        return jsonify({"status": "error", "message": "No models found"}), HTTPStatus.NOT_FOUND

    output = []

    for modeldb in models:
        model = ModelEntity(modeldb._id, modeldb.name, modeldb.formula, modeldb.description, modeldb.parameters, modeldb.linearizations)
        model_json = MODEL_SCHEMA.dump(model)
        output.append(model_json)

    response = {'models': output}
    return jsonify(response), HTTPStatus.OK

