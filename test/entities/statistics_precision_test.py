import numpy as np
import pytest

from entities.statistics import Statistics

Y_EXP = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0])
OFFSETS = np.array([1e-3, -1e-3, 2e-3, -2e-3, 1e-3, -1e-3])


def test_should_keep_small_sse_when_fit_is_almost_exact():
    y_pred = Y_EXP + OFFSETS

    stats = Statistics.all_statistics(Y_EXP, y_pred, num_params=2, aic=-50.0, bic=-48.0)

    # rel=1e-3: 4 significant figures are kept.
    assert stats["SSE"] == pytest.approx(float(np.sum(OFFSETS ** 2)), rel=1e-3)
    assert stats["SSE"] != 0.0
    assert stats["RMSE"] != 0.0


def test_should_round_large_statistics_to_fixed_decimals():
    stats = Statistics.all_statistics(Y_EXP, Y_EXP + OFFSETS, num_params=2, aic=-123.456789, bic=98.7654321)

    assert stats["AIC"] == pytest.approx(-123.4568, abs=1e-9)
    assert stats["BIC"] == pytest.approx(98.7654, abs=1e-9)
