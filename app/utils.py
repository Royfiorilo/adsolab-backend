import numpy as np
from scipy.interpolate import CubicSpline

ROUND_DIGIT = 4


def round_list_numbers(numbers, round=ROUND_DIGIT):
    return [round_number(num, round) for num in numbers]


def round_number(number, round_digit=ROUND_DIGIT):
    return round(number, round_digit)


def soft_curve(ce, qe_pred):
    interpolator = CubicSpline(ce, qe_pred)

    x = np.linspace(min(ce), max(ce), 100)
    x_combined = np.union1d(ce, x)
    y = interpolator(x_combined)
    return x, y

def process_adjustment_methods(adjustment_methods):
    for adjustment_method in adjustment_methods:
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