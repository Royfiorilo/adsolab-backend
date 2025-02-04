import logging
from typing import Dict

from database import Model, Linearization, Method
from entities.comparator import AdsorptionModelComparison
from entities.schemas.linearization_schema import LINEARIZATION_SCHEMA
from entities.schemas.model_schema import MODEL_SCHEMA
from exceptions.exceptions import NotFoundError
from services.sample_service import find_sample, filter_sample
from utils import round_list_numbers, round_number

def find_models() :
    models = Model.with_schema(None).all()
    if not models:
        raise NotFoundError('No models found')
    return models

def find_model(model_id: str):
    model = Model.with_schema(MODEL_SCHEMA).filter_by(_id=model_id).first()
    if not model:
        raise NotFoundError(f'Model {model_id} not found')
    return model

def find_methods():
    methods = Method.with_schema(None).all()
    if not methods:
        raise NotFoundError('No adjust methods found')
    return methods


def get_optimization_methods() -> Dict[str, str]:
    methods = find_methods()
    method_dict = {}

    for method in methods:
        method_dict[method.code] = method.description

    return method_dict









