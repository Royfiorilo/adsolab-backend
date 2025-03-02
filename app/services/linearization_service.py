import logging

from database import Linearization
from entities.schemas.linearization_schema import LINEARIZATION_SCHEMA
from exceptions.exceptions import NotFoundError
from services.model_service import find_model
from services.sample_service import find_sample, filter_sample
from utils import round_list_numbers, round_number


def process_linearization(linearization_id: str, sample, constants) -> dict:
    linearization = Linearization.with_schema(LINEARIZATION_SCHEMA).filter_by(
        linearization_id=linearization_id
    ).first()

    if linearization is None:
        error_msg = f"Linearization '{linearization_id}' not found"
        logging.error(error_msg)
        raise NotFoundError(error_msg)

    return linearization.run(sample, constants)


def format_linearization_result(*, name: str, id: str, x, y,
                                slope: float, intercept: float, vars,
                                params_info: tuple, statistics: dict) -> dict:
    parameters = [
        {
            "name": var,
            "value": round_number(params_info[0][var]),
            "std_err": round_number(params_info[1][var])
        }
        for var in vars
    ]

    return {
        "name": name,
        "id": id,
        "status": "OK",
        "transformed": {"x": x, "y": round_list_numbers(y)},
        "slope": slope,
        "intercept": intercept,
        "statistics": statistics,
        "parameters": parameters
    }


def compare_linearizations(linearization1, linearization2) -> dict:
    if not linearization1:
        return linearization2

    return linearization1 if abs(linearization1["statistics"]["r_squared"]) >= \
                             abs(linearization2["statistics"]["r_squared"]) else linearization2

def execute_linearizations(sample, linearizations, model_id: str) -> dict:
    model = find_model(model_id)
    constants = sample.constants

    linearization_results = []
    best_result = None
    result = {"model": model.name}

    for linearization_id in linearizations:
        solution = process_linearization(linearization_id, sample, constants)
        formatted_solution = format_linearization_result(**solution)
        linearization_results.append(formatted_solution)

        if formatted_solution["status"] == "OK":
            best_result = compare_linearizations(best_result, formatted_solution)
            result["best_result"] = best_result["id"]

    result["linearizations"] = linearization_results
    return result
