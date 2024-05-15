from flask import Flask, jsonify
import numpy as np

app = Flask(__name__)


def apply_langmuir(ce):
    return 0.198 * (0.189 * ce) / (1 + 0.189 * ce)


@app.route('/langmuir', methods=['GET'])
def test():
    ce = np.array([4.7, 7.0, 9.31, 16.6, 32.5, 62.8])
    apply_model = np.vectorize(apply_langmuir)
    results = list(apply_model(ce))
    return jsonify(results), 200


@app.after_request
def add_header(response):
    return response


if __name__ == '__main__':
    app.run()
