from http import HTTPStatus

from flask import jsonify, request
from flask_login import current_user

from app import create_app
from exceptions.exceptions import BadRequestError, NotFoundError, FilterSampleError

app = create_app()

@app.errorhandler(BadRequestError)
@app.errorhandler(FilterSampleError)
def handle_bad_request_error(e):
    return jsonify({
        "status": "ERROR",
        "message": e.message
    }), HTTPStatus.BAD_REQUEST


@app.errorhandler(NotFoundError)
def handle_not_found_error(e):
    return jsonify({
        "status": "ERROR",
        "message": e.message
    }), HTTPStatus.NOT_FOUND

# Overrides flask-security's response if user is already logged in.
@app.before_request
def modify_get_login_response():
    if request.path == "/login" and request.method == "GET" and current_user.is_authenticated:
        return jsonify({
                "user": {
                    "id": current_user.id,
                    "email": current_user.email
                }
            }), 200


if __name__ == '__main__':
    app.run(port=5000)
