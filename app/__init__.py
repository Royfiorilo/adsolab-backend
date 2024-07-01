from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from controler import model_controller, healt_check_controller
from .config import Config
from .config import Config

db = SQLAlchemy()


def create_app():
    app = Flask("adsolab")
    app.config.from_object(Config)
    db.init_app(app)

    with app.app_context():
        app.register_blueprint(model_controller.blueprint)
        app.register_blueprint(healt_check_controller.blueprint)
    return app
