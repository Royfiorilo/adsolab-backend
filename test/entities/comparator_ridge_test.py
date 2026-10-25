"""ABE-002: the Ridge combination that equilibrium still uses as its second criterion."""
from unittest.mock import patch

import numpy as np
from sklearn.model_selection import GridSearchCV
from sklearn.preprocessing import StandardScaler

from entities.comparator import AdsorptionModelComparison

CE = np.array([0.5, 1.0, 2.0, 4.0, 6.0, 8.0, 10.0, 15.0, 20.0])


def langmuir(ce, qmax=10.0, k=0.4):
    return qmax * k * ce / (1 + k * ce)


def freundlich(ce, kf=3.0, n=2.5):
    return kf * ce ** (1 / n)


def curves(*functions):
    return [f(CE) for f in functions], [f(np.linspace(0, CE.max(), 30)) for f in functions]


def test_should_never_return_a_negative_weight():
    """RIDGE-N01: the data are one curve minus another, so an unconstrained fit subtracts Freundlich."""
    y = 1.6 * langmuir(CE) - 0.6 * freundlich(CE)
    preds, extended = curves(langmuir, freundlich)

    result = AdsorptionModelComparison.get_ml_coefs_models(y, preds, extended)

    assert all(coef >= 0 for coef in result["coefs"])


def test_should_search_alpha_on_the_same_scaled_curves_as_the_final_fit():
    """RIDGE-H01: the call is the contract here (the old code searched on the unscaled curves)."""
    y = langmuir(CE)
    preds, extended = curves(langmuir, freundlich)
    seen = []
    original_fit = GridSearchCV.fit

    def spy(self, X, y_, **kwargs):
        seen.append(np.array(X))
        return original_fit(self, X, y_, **kwargs)

    with patch.object(GridSearchCV, "fit", spy):
        AdsorptionModelComparison.get_ml_coefs_models(y, preds, extended)

    expected = StandardScaler().fit_transform(np.column_stack(preds))
    # 1e-12: same transform, only floating point noise can differ.
    np.testing.assert_allclose(seen[0], expected, atol=1e-12)


def test_should_compare_a_sample_with_fewer_points_than_folds():
    """RIDGE-B01: 4 points used to raise inside GridSearchCV(cv=5) and end as a 500."""
    ce = CE[:4]
    y = langmuir(ce)

    result = AdsorptionModelComparison.get_ml_coefs_models(
        y, [langmuir(ce), freundlich(ce)], [langmuir(ce), freundlich(ce)])

    assert len(result["coefs"]) == 2


def test_should_compare_a_sample_too_small_to_cross_validate():
    """RIDGE-B02: one point cannot be split into folds, so the default alpha is used."""
    ce = CE[:1]

    result = AdsorptionModelComparison.get_ml_coefs_models(
        langmuir(ce), [langmuir(ce), freundlich(ce)], [langmuir(ce), freundlich(ce)])

    assert len(result["coefs"]) == 2
