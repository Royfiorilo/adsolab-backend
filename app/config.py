import os
from dotenv import load_dotenv

load_dotenv()  # Carga el archivo .env


class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    REACTORAPP_BASE_URL = 'https://laquisihereactorapp.fi.uba.ar'
    REACTORAPP_AUTH = '/api/auth/login'
    REACTORAPP_ADSORBATES = '/api/adsorbato/'
    REACTORAPP_ADSORBENTS = '/api/adsorbente/'
