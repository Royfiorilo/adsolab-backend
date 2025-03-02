import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from .config import Config

db = SQLAlchemy()


def create_app():
    app = Flask("adsolab")
    app.config.from_object(Config)
    db.init_app(app)
    env  = os.getenv('env')
    with app.app_context():
        from controller import model_controller, healt_check_controller, investigation_controller, sample_controller, materials_controller
        app.register_blueprint(model_controller.blueprint)
        app.register_blueprint(healt_check_controller.blueprint)
        app.register_blueprint(investigation_controller.blueprint)
        app.register_blueprint(sample_controller.blueprint)
        app.register_blueprint(materials_controller.blueprint)
        if env == 'development':
            db.create_all()
    return app
