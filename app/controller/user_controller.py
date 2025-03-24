from http import HTTPStatus

from flask import Blueprint, request, jsonify
from flask_login import current_user
from flask_security import auth_required, roles_accepted

from exceptions.exceptions import UsernameAlreadyTakenError, NotFoundError, BadRequestError
from services import user_service
from services.user_service import ADMIN_ROLE, DEV_ROLE

blueprint = Blueprint("user", __name__)


# Helper to validate email format
def is_valid_email(email):
    import re
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return bool(re.match(pattern, email))


@blueprint.route('/users', methods=['POST'])
@auth_required()
@roles_accepted(ADMIN_ROLE, DEV_ROLE)
def create_user():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'error': 'Email and password are required'}), HTTPStatus.BAD_REQUEST

    if not is_valid_email(email):
        return jsonify({'error': 'Invalid email format'}), HTTPStatus.BAD_REQUEST

    try:
        response = user_service.create_user(email=email, password=password, role=data.get('role'))
    except UsernameAlreadyTakenError as e:
        return jsonify({'error': e.message}), HTTPStatus.CONFLICT

    return jsonify(response), HTTPStatus.CREATED


@blueprint.route('/users', methods=['GET'])
@auth_required()
@roles_accepted(ADMIN_ROLE, DEV_ROLE)
def get_users():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    response = user_service.get_users(page, per_page)
    return jsonify(response), HTTPStatus.OK


@blueprint.route('/users/<int:user_id>', methods=['GET'])
@auth_required()
def get_user(user_id):
    if not (current_user.id == user_id or any(role.name == ADMIN_ROLE for role in current_user.roles)):
        return jsonify({'error': 'Unauthorized access'}), HTTPStatus.FORBIDDEN

    try:
        response = user_service.get_user(user_id)
    except NotFoundError as e:
        return jsonify({'error': e.message}), HTTPStatus.NOT_FOUND

    return jsonify(response), HTTPStatus.OK


@blueprint.route('/users/<int:user_id>', methods=['PUT'])
@auth_required()
def update_user(user_id):
    data = request.get_json()

    if 'email' in data and not is_valid_email(data['email']):
        return jsonify({'error': 'Invalid email format'}), HTTPStatus.BAD_REQUEST

    try:
        response = user_service.update_user(user_id, data, current_user)
    except NotFoundError as e:
        return jsonify({'error': e.message}), HTTPStatus.NOT_FOUND
    except UsernameAlreadyTakenError as e:
        return jsonify({'error': e.message}), HTTPStatus.CONFLICT
    except BadRequestError as e:
        return jsonify({'error': e.message}), HTTPStatus.BAD_REQUEST

    return jsonify(response), HTTPStatus.OK


@blueprint.route('/users/<int:user_id>', methods=['DELETE'])
@auth_required()
@roles_accepted(ADMIN_ROLE, DEV_ROLE)
def delete_user(user_id):
    if current_user.id == user_id:
        return jsonify({'error': 'Cannot delete your own account'}), HTTPStatus.BAD_REQUEST

    try:
        response = user_service.delete_user(user_id)
    except NotFoundError as e:
        return jsonify({'error': e.message}), HTTPStatus.NOT_FOUND

    return jsonify(response)
