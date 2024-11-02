from database import Model
from exceptions.exceptions import NotFoundError


def find_models():
    models  = Model.with_schema(None).all()
    if not models:
        raise NotFoundError('No models found')
    return models