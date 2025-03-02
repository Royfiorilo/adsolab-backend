from flask import Blueprint, jsonify, make_response

blueprint = Blueprint("health-check", __name__)


@blueprint.route('/', methods=['GET'])
def root():
    return make_response('', 204)

@blueprint.route('/health-check', methods=['GET'])
def health_check():
    return jsonify({"status": "ok"})
