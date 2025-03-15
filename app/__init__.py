import os

import flask_wtf
from flask import Flask
from flask_cors import CORS
from flask_security import SQLAlchemyUserDatastore, Security, hash_password

from database import db, User, Role
from .config import Config

user_datastore = SQLAlchemyUserDatastore(db, User, Role)


def create_app():
    app = Flask("adsolab")
    app.config.from_object(Config)

    db.init_app(app)

    flask_wtf.CSRFProtect(app)
    app.security = Security(app, user_datastore)

    CORS(app, supports_credentials=True, methods=["GET", "POST", "OPTIONS"])

    env = os.getenv('env')
    with app.app_context():
        from controler import model_controller, healt_check_controller, investigation_controller, sample_controller, \
            materials_controller, auth_controller
        app.register_blueprint(model_controller.blueprint)
        app.register_blueprint(healt_check_controller.blueprint)
        app.register_blueprint(investigation_controller.blueprint)
        app.register_blueprint(sample_controller.blueprint)
        app.register_blueprint(materials_controller.blueprint)
        app.register_blueprint(auth_controller.blueprint)
        if env == 'development':
            db.create_all()
        # Create User to test with
        test_user_email = os.getenv('TEST_USER_EMAIL')
        test_user_password = os.getenv('TEST_USER_PASSWORD')
        if not app.security.datastore.find_user(email=test_user_email):
            app.security.datastore.create_user(email=test_user_email,
                                               password=hash_password(test_user_password))
            db.session.commit()
    return app
