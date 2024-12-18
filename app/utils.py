import numpy as np
from mpl_toolkits.mplot3d.proj3d import transform
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

def soft_curves(results):
    for result in results:
        x,y = soft_curve(result["transformed"]["x"], result["transformed"]["y"])
        transformed = {"x": round_list_numbers(x), "y": round_list_numbers(y)}
        result["transformed"] = transformed
