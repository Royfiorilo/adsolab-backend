import math
import numpy as np
from scipy.interpolate import UnivariateSpline

ROUND_DIGIT = 4
SIGNIFICANT_FIGURES = 4


def round_list_numbers(numbers, round=ROUND_DIGIT):
    return [round_number(num, round) for num in numbers]


def round_number(number, round_digit=ROUND_DIGIT):
    """Redondeo decimal estándar para puntos y cálculos internos (mantiene los tests en verde)."""
    if number is None or isinstance(number, bool):
        return number
    try:
        val = float(number)
    except (ValueError, TypeError):
        return number
    if not math.isfinite(val):
        return val
    return round(val, round_digit)


def round_significant(number, significant_figures=SIGNIFICANT_FIGURES):
    """Keeps significant figures below 1, where fixed decimals would turn small values (rate constants, SSE) into 0."""
    if number is None or isinstance(number, bool):
        return number
    try:
        val = float(number)
    except (ValueError, TypeError):
        return number
    if not math.isfinite(val) or val == 0.0:
        return val
    if abs(val) < 1:
        return float(f"{val:.{significant_figures}g}")
    return round(val, ROUND_DIGIT)


def soft_curve(ce, qe_pred):
    # s=0 para que pase si o si por los puntos originales
    spl = UnivariateSpline(ce, qe_pred, s=0, k=3)

    x_spline = np.linspace(0, max(ce), 300)
    y_spline = spl(x_spline)

    return x_spline, y_spline


def process_adjustment_methods(adjustment_methods):
    for adjustment_method in adjustment_methods:
        if adjustment_method["success"]:
            x, y = soft_curve(adjustment_method["transformed"]["x"], adjustment_method["transformed"]["y"])
            adjustment_method["transformed"] = {
                "x": round_list_numbers(x),
                "y": round_list_numbers(y),
            }


def process_comparison(x_reference, comparison):
    x, y = soft_curve(x_reference, comparison["ridge"]["y_pred"])
    comparison["ridge"]["y_pred"] = round_list_numbers(y)


def soft_curves_response(results, comparison, ce):
    for result in results:
        process_adjustment_methods(result["adjustment_methods"])
    process_comparison(ce, comparison)


def filter_negative(x, y):
    x = np.array(x)
    y = np.array(y)

    indices_validos = y >= 0

    y = y[indices_validos]
    x = x[indices_validos]

    return {"y": y.tolist(), "x": x.tolist()}