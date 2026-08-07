import app  # noqa: F401  debe ir primero: rompe el ciclo dump_mixin -> app -> database

from http import HTTPStatus
from unittest.mock import MagicMock, patch

import flask_security
import pytest
from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException

TEST_USER_ID = 1


def _bypass_auth(*args, **kwargs):
    def decorator(view):
        return view
    return decorator


# Los controllers aplican estos decoradores al importarse y la app de test no inicializa
# flask_security, así que hay que anularlos antes de importar los blueprints.
flask_security.auth_required = _bypass_auth
flask_security.roles_required = _bypass_auth
flask_security.roles_accepted = _bypass_auth

from controller.investigation_controller import blueprint as bp_investigation_controller
from controller.materials_controller import blueprint as bp_materials_controller
from controller.model_controller import blueprint as bp_model_controller
from controller.sample_controller import blueprint as bp_sample_controller
from exceptions.exceptions import BadRequestError, NotFoundError


@pytest.fixture
def app():
    app = Flask("adsolab_test")
    app.register_blueprint(bp_investigation_controller)
    app.register_blueprint(bp_sample_controller)
    app.register_blueprint(bp_model_controller)
    app.register_blueprint(bp_materials_controller)
    app.testing = True
    app.user_datastore = MagicMock()

    @app.errorhandler(BadRequestError)
    def handle_bad_request(error):
        return jsonify({"status": "error", "message": str(error)}), HTTPStatus.BAD_REQUEST

    @app.errorhandler(NotFoundError)
    def handle_not_found(error):
        return jsonify({"status": "error", "message": str(error)}), HTTPStatus.NOT_FOUND

    @app.errorhandler(Exception)
    def handle_generic_exception(error):
        if isinstance(error, HTTPException):
            return error
        return jsonify({"status": "error", "message": str(error)}), HTTPStatus.INTERNAL_SERVER_ERROR

    return app


@pytest.fixture
def mock_db():
    with patch('database.db') as mock_db:
        mock_db.session = MagicMock()
        yield mock_db


@pytest.fixture
def mock_hash_password():
    with patch('flask_security.utils.hash_password') as mock_hash:
        mock_hash.return_value = 'hashed_password'
        yield mock_hash

@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture(autouse=True)
def mock_current_user():
    user = MagicMock()
    user.id = TEST_USER_ID
    with patch('controller.sample_controller.current_user', user), \
            patch('controller.investigation_controller.current_user', user):
        yield user


@pytest.fixture
def investigation_id():
    return 1


@pytest.fixture
def mock_investigation(investigation_id):
    return {
        "investigation_id": investigation_id,
        "sample_id": 1
    }


@pytest.fixture
def mock_sample():
    sample = MagicMock()
    sample.sample_id = 1
    sample.ce = [0, 0.0067763, 0.015759, 0.0316021, 0.041034, 0.1198222, 0.1371802, 0.289058, 0.36124, 0.420855]
    sample.qe = [0, 0.0259714, 0.035572, 0.0428751, 0.068788, 0.0732422, 0.092398, 0.14434, 0.1301768, 0.161924]
    sample.adsorbent_id = 1
    sample.adsorbate_id = 3
    sample.deleted_at = None
    return sample

@pytest.fixture
def mock_samples():
    sample_1 = MagicMock()
    sample_1.sample_id = 1
    sample_1.ce = [0, 0.0067763, 0.015759, 0.0316021, 0.041034, 0.1198222, 0.1371802, 0.289058, 0.36124, 0.420855]
    sample_1.qe = [0, 0.0259714, 0.035572, 0.0428751, 0.068788, 0.0732422, 0.092398, 0.14434, 0.1301768, 0.161924]
    sample_1.adsorbent_id = 1
    sample_1.adsorbate_id = 3

    sample_2 = MagicMock()
    sample_2.sample_id = 2
    sample_2.ce = [0, 0.0067763, 0.015759, 0.0316021, 0.041034, 0.1198222, 0.1371802, 0.289058, 0.36124, 0.420855]
    sample_2.qe = [0, 0.0259714, 0.035572, 0.0428751, 0.068788, 0.0732422, 0.092398, 0.14434, 0.1301768, 0.161924]
    sample_2.adsorbent_id = 4
    sample_2.adsorbate_id = 2
    return [sample_1, sample_2]


@pytest.fixture
def mock_models():
    model_1 = MagicMock()
    model_1.id = 1
    model_1.name = "Langmuir"
    model_1.formula = "qe = qmax * k * ce / (1 + (k * ce))"
    model_1.constants = None
    model_1.parameters = {"qmax": "es un parámetro que representa la máxima cantidad de adsorbato", "k": "es la constante de equilibrio"}

    model_2 = MagicMock()
    model_2.id = 2
    model_2.name = "Temkin"
    model_2.formula = "qe = ((R * T)/btk) * ln(ktk * ce)"
    model_2.constants = ["R","T"]
    model_2.parameters = {"btk": "parámetro que está directamente relacionado con el calor de adsorción.", "ktk": "constante de equilibrio de adsorción del modelo."}

    return [model_1, model_2]


@pytest.fixture
def mock_methods():
    method_1 = MagicMock()
    method_1.id = 1
    method_1.name = "COBYLA"
    method_1.code = "cobyla"
    method_1.color = "#OOFFFF"

    method_2 = MagicMock()
    method_2.id = 2
    method_2.name = "Nelder-Mead"
    method_2.code = "nelder"
    method_2.color = "#FFFF00"

    return [method_1, method_2]


@pytest.fixture
def mock_version():
    version = MagicMock()
    version.version_id = 1
    return version


@pytest.fixture
def version_id():
    return 1


@pytest.fixture
def valid_fitted_method_data():
    return {
        "name": "cg",
        "parameters": [
            {
                "name": "k",
                "std_err": 19.46,
                "value": 97.2328
            },
            {
                "name": "qmax",
                "std_err": 0.0021,
                "value": 0.0323
            }
        ],
        "statistics": {
            "AIC": -114.267,
            "BIC": -113.8725,
            "HYBRID": 0.0192,
            "RMSE": 0.0014,
            "SSE": 0.0,
            "adjust_chi_squeared": 0.0011,
            "adjust_r_squared": 0.9254,
            "chi_squared": 0.0074,
            "r_squared": 0.944},
        "residuals": {
            "analysis": {
                "durbin_watson": 1.7846,
                "homoscedasticity_pvalue": 0.0011,
                "normality_pvalue": 0.9115,
                "passes_homoscedasticity": 1,
                "passes_independence": 0,
                "passes_normality": 0
            },
            "values": [
                -0.002360731738398178,
                0.0008868234169948277,
                0.00033092827427115556,
                -0.0014061007434928406,
                0.002196183489489134,
                0.001338124768325493,
                1.453825896606184e-05,
                -0.00013469345823400106,
                -0.0016103666003053872
            ]
        }
    }


@pytest.fixture
def valid_comparison_data():
    return {
        "comparison_id": 1,
        "heuristic": {
            "best_model": 3,
            "results": [
                {
                    "model": 1,
                    "score": 214.3872
                },
                {
                    "model": 2,
                    "score": 130.5352
                },
                {
                    "model": 3,
                    "score": 300.1018
                },
                {
                    "model": 5,
                    "score": 300.1018
                },
                {
                    "model": 4,
                    "score": 187.6014
                }
            ]
        },
        "ridge": {
            "best_model": 1,
            "residuals": {
                "analysis": {
                    "durbin_watson": 2.6162,
                    "homoscedasticity_pvalue": 0.0099,
                    "normality_pvalue": 0.5129,
                    "passes_homoscedasticity": 1,
                    "passes_independence": 1,
                    "passes_normality": 0
                },
                "values": [
                    -8.620758365434755e-05,
                    0.0006714951976932535,
                    -0.00015873015402497262,
                    -0.001750361198537758,
                    0.0011967432363107766,
                    0.0005297048708447182,
                    -0.0004756018083781552,
                    0.00019891234905944008,
                    -0.0001259549093129697
                ]
            },
            "results": [
                {
                    "coef": 0.0234,
                    "model": 1
                },
                {
                    "coef": 0.0195,
                    "model": 2
                },
                {
                    "coef": 0.0119,
                    "model": 3
                },
                {
                    "coef": 0.0016,
                    "model": 5
                },
                {
                    "coef": 0.0148,
                    "model": 4
                }
            ],
            "statistics": {
                "AIC": -93.163,
                "BIC": -92.1769,
                "HYBRID": 0.0071,
                "RMSE": 0.0008,
                "SSE": 0.0,
                "adjust_chi_squeared": 0.0004,
                "adjust_r_squared": 0.9532,
                "chi_squared": 0.0016,
                "r_squared": 0.9824
            },
            "y_pred": [
                -0.3196,
                -0.0491,
                -0.0374,
                -0.03,
                -0.0251,
                -0.0209,
                -0.0175,
                -0.0147,
                -0.0119,
                -0.0096,
                -0.0081,
                -0.0063,
                -0.0047
            ]
        }
    }



@pytest.fixture
def valid_fitted_model_data(valid_fitted_method_data):
    return {
        "model": 1,
        "best_adjust": "cg",
        "adjustment_methods": [valid_fitted_method_data],
        "parameters": [{
            "name": "k",
            "value": 96.7092,
            "stderr": 0.0002
        }, {
            "name": "qmax",
            "value": 0.0318,
            "stderr": 1949.9258
        }],
        "transformed":{"x":[0.1,0.2,0.3], "y": [0.1,0.2,0.3] },
    }


@pytest.fixture
def valid_version_data(investigation_id, version_id, valid_fitted_model_data, valid_comparison_data):
    return {
        "version_id": version_id,
        "investigation_id": investigation_id,
        "iterations": 1000,
        "steps": 5,
        "created_at": "2025-03-01T12:00:00",
        "results": [valid_fitted_model_data],
        "comparison": valid_comparison_data
    }


@pytest.fixture
def invalid_version_data(investigation_id, version_id):

    return {
        "version_id": version_id,
        "investigation_id": investigation_id,
        "created_at": "2025-03-01T12:00:00",
    }


@pytest.fixture
def versions_list(valid_version_data):
    version1 = dict(valid_version_data)
    version1["version_id"] = 1

    version2 = dict(valid_version_data)
    version2["version_id"] = 2

    return [version1, version2]

@pytest.fixture
def valid_linear_model_data(valid_fitted_model_data):
    return {
    "investigation_id": 1,
    "results": [
        {
            "best_result": 1,
            "linearizations": [
                {
                    "id": 1,
                    "intercept": 0.3248498808714019,
                    "name": "HaneseWoolf Linearization",
                    "parameters": [
                        {
                            "name": "k",
                            "std_err": 0.0002,
                            "value": 96.7092
                        },
                        {
                            "name": "qmax",
                            "std_err": 1949.9258,
                            "value": 0.0318
                        }
                    ],
                    "slope": 31.41597578455716,
                    "statistics": {
                        "r_squared": 0.9731
                    },
                    "status": "OK",
                    "transformed": {
                        "x": [
                            0.0042,
                            0.0084,
                            0.0097,
                            0.0155,
                            0.0214,
                            0.0222,
                            0.0346,
                            0.0382,
                            0.0493
                        ],
                        "y": [
                            0.6,
                            0.5455,
                            0.6062,
                            0.8611,
                            0.8917,
                            0.9487,
                            1.3896,
                            1.5099,
                            1.9641
                        ]
                    }
                },
                {
                    "id": 2,
                    "intercept": 23.181042742026357,
                    "name": "Lineweaver-Burk Linearization",
                    "parameters": [
                        {
                            "name": "k",
                            "std_err": 0.0004,
                            "value": 49.942
                        },
                        {
                            "name": "qmax",
                            "std_err": 2189.4348,
                            "value": 0.0431
                        }
                    ],
                    "slope": 0.46415946728156676,
                    "statistics": {
                        "r_squared": 0.9498
                    },
                    "status": "OK",
                    "transformed": {
                        "x": [
                            238.0952,
                            119.0476,
                            103.0928,
                            64.5161,
                            46.729,
                            45.045,
                            28.9017,
                            26.178,
                            20.284
                        ],
                        "y": [
                            142.8571,
                            64.9351,
                            62.5,
                            55.5556,
                            41.6667,
                            42.735,
                            40.1606,
                            39.5257,
                            39.8406
                        ]
                    }
                }
            ],
            "model": "Langmuir"
        },
        {
            "best_result": 3,
            "linearizations": [
                {
                    "id": 3,
                    "intercept": -2.0472152556544665,
                    "name": "Freundlich Linearization",
                    "parameters": [
                        {
                            "name": "kf",
                            "std_err": 2.4419,
                            "value": 0.1291
                        },
                        {
                            "name": "nf",
                            "std_err": 0.0176,
                            "value": 2.0885
                        }
                    ],
                    "slope": 0.4788050949806523,
                    "statistics": {
                        "r_squared": 0.8477
                    },
                    "status": "OK",
                    "transformed": {
                        "x": [
                            -5.4727,
                            -4.7795,
                            -4.6356,
                            -4.1669,
                            -3.8444,
                            -3.8077,
                            -3.3639,
                            -3.2649,
                            -3.0098
                        ],
                        "y": [
                            -4.9618,
                            -4.1734,
                            -4.1352,
                            -4.0174,
                            -3.7297,
                            -3.755,
                            -3.6929,
                            -3.677,
                            -3.6849
                        ]
                    }
                }
            ],
            "model": "Freundlich"
        },
        {
            "best_result": 3,
            "linearizations": [
                {
                    "id": 3,
                    "intercept": -2.0472152556544665,
                    "name": "Freundlich Linearization",
                    "parameters": [
                        {
                            "name": "kf",
                            "std_err": 2.4419,
                            "value": 0.1291
                        },
                        {
                            "name": "nf",
                            "std_err": 0.0176,
                            "value": 2.0885
                        }
                    ],
                    "slope": 0.4788050949806523,
                    "statistics": {
                        "r_squared": 0.8477
                    },
                    "status": "OK",
                    "transformed": {
                        "x": [
                            -5.4727,
                            -4.7795,
                            -4.6356,
                            -4.1669,
                            -3.8444,
                            -3.8077,
                            -3.3639,
                            -3.2649,
                            -3.0098
                        ],
                        "y": [
                            -4.9618,
                            -4.1734,
                            -4.1352,
                            -4.0174,
                            -3.7297,
                            -3.755,
                            -3.6929,
                            -3.677,
                            -3.6849
                        ]
                    }
                }
            ],
            "model": "Freundlich"
        }
    ]
}
