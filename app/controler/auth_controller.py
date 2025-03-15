from flask import Blueprint, jsonify, make_response, current_app, request, after_this_request
from flask_login import user_logged_in, user_loaded_from_cookie, current_user
from flask_security import verify_and_update_password

from app import User

blueprint = Blueprint("auth", __name__)

@blueprint.route('/auth-token', methods=['POST'])
def get_auth_token():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    user = User.query.filter_by(email=email).first()

    if user and verify_and_update_password(password, user):
        token = user.get_auth_token()
        return jsonify({"token": token, "user_id": user.id, "email": user.email}), 200
    else:
        return jsonify({"error": "Invalid email or password"}), 401

@user_logged_in.connect
def after_login(sender, user):

    @after_this_request
    def modify_response(response):
        if response.is_json:
            new_response = {
                "user": {
                    "id": user.id,
                    "email": user.email
                }
            }
            response.set_data(jsonify(new_response).get_data())
        return response
