from flask import Blueprint, request, jsonify

blueprint = Blueprint('investigation', __name__)

@blueprint.route('/investigation/sample', methods=['POST'])
def create_investigation():
    request_json = request.get_json()

    return jsonify(request_json), 200

