import os
import secrets

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
    SECRET_KEY = secrets.token_urlsafe()
    SECURITY_PASSWORD_SALT = secrets.SystemRandom().getrandbits(128).to_bytes(128, 'big')
    WTF_CSRF_CHECK_DEFAULT = False
    SECURITY_CSRF_PROTECT_MECHANISMS = ["session"]
    SECURITY_CSRF_COOKIE_NAME = "XSRF-TOKEN"
    WTF_CSRF_TIME_LIMIT = None
    # --- Flask Security ---

    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True
    }
