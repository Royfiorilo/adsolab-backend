from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from .config import Config

db = SQLAlchemy()

def create_app():
    app = Flask("adsolab")
    app.config.from_object(Config)
    db.init_app(app)

    with app.app_context():
        from . import routes  # Importar el Blueprint aquí
        app.register_blueprint(routes.app)
    return app