from http import HTTPStatus

from flask import jsonify

from app import create_app
from exceptions.exceptions import BadRequestError, NotFoundError, FilterSampleError

app = create_app()
@app.after_request
def add_header(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = '*'
    response.headers['Access-Control-Allow-Headers'] = '*'
    return response


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



if __name__ == '__main__':
    app.run(port=5000)
