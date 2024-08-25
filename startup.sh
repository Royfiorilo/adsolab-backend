#!/bin/sh

source $(pipenv --venv)/bin/activate
export FLASK_APP=start.py
export PYTHONPATH=/app
flask run --host=0.0.0.0