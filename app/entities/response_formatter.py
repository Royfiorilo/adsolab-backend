from entities.no_linear_model import FitResult


class ResponseFormatter:
    @staticmethod
    def format_fit_result(fit_result: FitResult) -> dict:
        fit_result.clean_transformed()
        return {
            "name": fit_result.method_name,
            "description": fit_result.method_description,
            "success": fit_result.success,
            "parameters": fit_result.parameters,
            "statistics": fit_result.statistics,
            "residuals": fit_result.residuals,
            "transformed": fit_result.transformed
        }

