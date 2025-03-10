import os

from dotenv import load_dotenv

load_dotenv()  # Carga el archivo .env


class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    REACTORAPP_BASE_URL = os.getenv('REACTORAPP_BASE_URL')
    REACTORAPP_AUTH = os.getenv('REACTORAPP_AUTH')
    REACTORAPP_ADSORBATES = os.getenv('REACTORAPP_ADSORBATES')
    REACTORAPP_ADSORBENTS = os.getenv('REACTORAPP_ADSORBENTS')

    # --- Flask Security ---
    SECRET_KEY = os.getenv('SECRET_KEY')
    SECURITY_PASSWORD_SALT = os.getenv('SECURITY_PASSWORD_SALT')
    WTF_CSRF_CHECK_DEFAULT = False
    SECURITY_CSRF_PROTECT_MECHANISMS = ["session"]
    SECURITY_CSRF_COOKIE_NAME = "XSRF-TOKEN"
    SECURITY_CSRF_COOKIE = {"samesite": "None", "httponly": False, "secure": True,
                            "domain": os.getenv('DOMAIN', 'localhost')}
    WTF_CSRF_TIME_LIMIT = None
    REMEMBER_COOKIE_SAMESITE = "None"
    SESSION_COOKIE_SAMESITE = "None"
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_DOMAIN = os.getenv('DOMAIN', 'localhost')
    # --- Flask Security ---

    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True
    }
