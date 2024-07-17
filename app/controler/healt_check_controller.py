from flask import Blueprint, jsonify

blueprint = Blueprint("health-check", __name__)


@blueprint.route('/health-check', methods=['GET'])
def health_check():
    return jsonify({"status": "ok"})
