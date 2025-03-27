import os

import flask_wtf
from flask import Flask
from flask_cors import CORS
from flask_security import SQLAlchemyUserDatastore, Security, hash_password

from database import db, User, Role
from services.user_service import ADMIN_ROLE, DEV_ROLE
from .config import Config

user_datastore = SQLAlchemyUserDatastore(db, User, Role)


def create_app():
    app = Flask("adsolab")
    app.config.from_object(Config)

    db.init_app(app)

    flask_wtf.CSRFProtect(app)
    app.security = Security(app, user_datastore)

    CORS(app, supports_credentials=True, methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])

    env = os.getenv('env')
    with app.app_context():
        from controller import model_controller, healt_check_controller, investigation_controller, sample_controller, \
            materials_controller, auth_controller, user_controller
        app.register_blueprint(model_controller.blueprint)
        app.register_blueprint(healt_check_controller.blueprint)
        app.register_blueprint(investigation_controller.blueprint)
        app.register_blueprint(sample_controller.blueprint)
        app.register_blueprint(materials_controller.blueprint)
        app.register_blueprint(auth_controller.blueprint)
        app.register_blueprint(user_controller.blueprint)
        if env == 'development':
            db.create_all()

        # Create User to test with
        test_user_email = os.getenv('TEST_USER_EMAIL')
        test_user_password = os.getenv('TEST_USER_PASSWORD')
        if not app.security.datastore.find_user(email=test_user_email):
            user = app.security.datastore.create_user(email=test_user_email,
                                                      password=hash_password(test_user_password))
            app.security.datastore.add_role_to_user(user, ADMIN_ROLE)
            db.session.commit()

        # Create User Dev  Admin
        dev_user_email = os.getenv('DEV_USER_EMAIL')
        dev_user_password = os.getenv('DEV_USER_PASSWORD')
        if not app.security.datastore.find_user(email=dev_user_email):
            user = app.security.datastore.create_user(email=dev_user_email,
                                                      password=hash_password(dev_user_password))
            app.security.datastore.add_role_to_user(user, DEV_ROLE)
            db.session.commit()

    return app
