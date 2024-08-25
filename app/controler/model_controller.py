from flask import jsonify, request, Blueprint
import numpy as np
from http import HTTPStatus
from models.models import *
from entities.model import Model as ModelEntity
from entities.schemas.model_schema import MODEL_SCHEMA
from database import Model


blueprint = Blueprint('model', __name__)


@blueprint.route('/run-model/<model_name>', methods=['POST'])
def run_model(model_name):
    data = request.get_json()
    dots_ce = data['ce']
    dots_qe = data['qe']

    ce = np.array(dots_ce)
    qe = np.array(dots_qe)

    modeldb = Model.query.filter_by(name=model_name).first()
    model = ModelEntity(modeldb._id, modeldb.name, modeldb.formula, modeldb.description, modeldb.parameters,
                        modeldb.linearizations)

    if not model:
        return jsonify({"status": "error", "message": "Model not found"}), HTTPStatus.NOT_FOUND

    linearizations = Linearization.query.filter_by(model_id=model.id).all()
    r2 = 0
    q_max = 0
    k = 0
    linearization_name = ''
    linearization_formula = ''


    match model_name.lower():
        case 'langmuir':
            for linearizationdb in linearizations:
                linearization = LinearizationEntity(
                    linearizationdb.linearization_id,
                    linearizationdb.name,
                    linearizationdb.formula,
                    linearizationdb.description,
                    linearizationdb.parameters)

                #Acá habría que ejecutar cada una de las linealizaciones
                k_actual, qmax_actual, r_value = langmuir_linearizations(linearization.name, ce, qe)

                #Si el R2 de la linealización es mejor que la anterior, me quedo con esos parámetros
                #para ejecutar el modelo.
                if r_value ** 2 > r2:
                    r2 = r_value ** 2
                    k = k_actual
                    q_max = qmax_actual
                    linearization_name = linearization.name
                    linearization_formula = linearization.formula

            apply_model = np.vectorize(langmuir)
            qe_model = list(apply_model(q_max, k, ce))
        case _:
            return jsonify({"status": "error", "message": "Model not implemented"}), HTTPStatus.NOT_FOUND

    response = {
        "ce": dots_ce,
        "qe": qe_model,
        "formula": model.formula,
        "linearization_name": linearization_name,
        "linearization_formula": linearization_formula
    }
    return jsonify(response), HTTPStatus.OK


@blueprint.route('/models', methods=['GET'])
def get_models():
    models = Model.with_schema(MODEL_SCHEMA).all()

    if not models:
        return jsonify({"status": "error", "message": "No models found"}), HTTPStatus.NOT_FOUND

    output = []

    for model in models:
        model_json = MODEL_SCHEMA.dump(model)
        output.append(model_json)

    response = {'models': output}
    return jsonify(response), HTTPStatus.OK
