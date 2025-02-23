from typing import TypedDict

from entities.response_formatter import ResponseFormatter
from exceptions.exceptions import LinearizationError
from services.model_service import find_model, get_optimization_methods
from services.sample_service import find_sample, filter_sample


class ModelData(TypedDict):
    model: str
    seeds: list
    iterations: None
    step: None


class ModelResult(TypedDict):
    model: str
    adjustments: list
    best_adjust: str


class FormattedResult(TypedDict):
    adjustment_methods: list
    best_adjust: str
    model: str


class ErrorResult(TypedDict):
    model: str
    error: str


def format_adjustment_methods(result: ModelResult) -> FormattedResult:
    return { "adjustment_methods": [
            ResponseFormatter.format_fit_result(fit_result)
            for fit_result in result["adjustments"]
        ],
        "best_adjust": result["best_adjust"],
        "model": result["model"],
    }


def format_results(results) -> list[FormattedResult]:
    return [
        format_adjustment_methods(result)
        for result in results
        if "error" not in result
    ]


def process_model(model_config: ModelData, sample: object, methods: dict, constants: dict):
    model = find_model(model_config['model'])

    results = model.run(
        sample=sample,
        seeds=model_config['seeds'],
        methods=methods,
        constants=constants,
        step=model_config.get('step'),
        iterations=model_config.get('iterations')
    )

    return results, model


def prepare_model_execution(investigation: object,filter_params):
    methods = get_optimization_methods()

    sample = find_sample(investigation.sample_id)
    if filter_params:
        filter_sample(sample, filter_params)

    return sample, methods


def format_model_result(model_config: ModelData,fit_results: list,model) -> ModelResult:
    return {
        "model": model_config['model'],
        "adjustments": fit_results,
        "best_adjust": model.get_best_method_name()
    }


def exec_no_linear_model(investigation,model_data: ModelData, filter_params = None):
    try:

        sample, methods = prepare_model_execution(investigation, filter_params)
        constants = investigation.constants
        fit_results, model = process_model(model_data, sample, methods, constants)

        model_result = format_model_result(model_data, fit_results, model)

        return model_result, model
    except LinearizationError as e:
        error_result = {"model": model_data["model"], "error": str(e)}
        return error_result, None


def process_models(investigation,models_data,filter_params):
    results = []
    successful_models = []

    for model_data in models_data:
        result, model = exec_no_linear_model(investigation, model_data, filter_params)
        results.append(result)
        if model is not None:
            successful_models.append(model)

    return results, successful_models


