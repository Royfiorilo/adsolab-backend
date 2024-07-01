from flask import jsonify, request, Blueprint
import numpy as np
from app.entities.model import Model

blueprint = Blueprint('model', __name__)


def apply_langmuir(ce):
    return 0.198 * (0.189 * ce) / (1 + 0.189 * ce)


@blueprint.route('/run-model/<model_name>', methods=['POST'])
def run_model(model_name):
    data = request.get_json()
    dot_x = data['x']
    x = np.array(dot_x)

    apply_model = np.vectorize(apply_langmuir)
    y_model = list(apply_model(x))

    model = Model.query.filter_by(name=model_name).first()
    if not model:
        return jsonify({"status": "error", "message": "Model not found"}), 404

    response = {
        "x": dot_x,
        "y": y_model,
        "formula": model.formula
    }

    return jsonify(response), 200


@blueprint.route('/models', methods=['GET'])
def get_models():
    models = Model.query.all()
    if not models:
        return jsonify({"status": "error", "message": "No models found"}), 404
    output = []
    for model in models:
        model_json = {'id': model.id, 'name': model.name, 'formula': model.formula}
        output.append(model_json)
    response = {'models': output}
    return jsonify(response), 200

