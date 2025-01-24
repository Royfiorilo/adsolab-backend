import os
from dotenv import load_dotenv

load_dotenv()  # Carga el archivo .env


class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    REACTORAPP_BASE_URL = os.getenv('REACTORAPP_BASE_URL')
    REACTORAPP_AUTH =  os.getenv('REACTORAPP_AUTH')
    REACTORAPP_ADSORBATES = os.getenv('REACTORAPP_ADSORBATES')
    REACTORAPP_ADSORBENTS = os.getenv('REACTORAPP_ADSORBENTS')