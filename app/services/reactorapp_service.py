import requests
from flask import current_app
import os

BASE_URL = os.environ.get('REACTORAPP_BASE_URL')

def get_auth():

    auth_endpoint = os.environ.get('REACTORAPP_AUTH')

    credentials = {
        "email": os.environ.get("REACTORAPP_USER"),
        "password": os.environ.get("REACTORAPP_PASS")
    }
    response = requests.post(BASE_URL+auth_endpoint, json=credentials)
    return response

def get_adsorbents():
    auth_json = get_auth().json()

    adsorbents_endpoint = os.environ.get('REACTORAPP_ADSORBENTS')

    headers = {
        "Authorization" : 'Bearer ' + auth_json['accessToken']
    }

    response = requests.get(BASE_URL+adsorbents_endpoint, headers=headers)
    return response.json()


def get_adsorbates():
    auth_json = get_auth().json()
    adsorbates_endpoint = os.environ.get('REACTORAPP_ADSORBATES')

    headers = {
        "Authorization": 'Bearer ' + auth_json['accessToken']

    }

    response = requests.get(BASE_URL + adsorbates_endpoint, headers=headers)
    return response.json()