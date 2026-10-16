"""Standard errors of parameters solved from a fitted line (delta method), shared by both modules."""
import math
from typing import Dict, Optional

import numpy as np
from sympy import diff

# The line gives two numbers (slope and intercept), so the error is defined for two unknowns.
LINE_UNKNOWNS = 2


def line_covariance(result_lr, x_values) -> np.ndarray:
    """Covariance of (slope, intercept) of an ordinary least-squares line: cov(m, b) = -mean(x) * var(m)."""
    var_m = result_lr.stderr ** 2
    cov_mb = -float(np.mean(x_values)) * var_m
    return np.array([[var_m, cov_mb], [cov_mb, result_lr.intercept_stderr ** 2]])


def propagate_std_errors(m_expr, b_expr, params: Dict[str, float], covariance) -> Dict[str, Optional[float]]:
    """
    Std err of each parameter θ solved from slope = m(θ) and intercept = b(θ).

    The delta method needs ∂θ/∂(m, b), the inverse of the Jacobian ∂(m, b)/∂θ that the expressions
    give. Every error is None when it cannot be computed (not two unknowns, singular Jacobian,
    non-finite result).
    """
    names = sorted(params)
    unknown = {s.name: s for s in (m_expr.free_symbols | b_expr.free_symbols) if s.name in params}
    if len(names) != LINE_UNKNOWNS or set(unknown) != set(names):
        return {name: None for name in names}

    values = {unknown[name]: params[name] for name in names}
    try:
        forward = np.array([
            [float(diff(expr, unknown[name]).subs(values)) for name in names]
            for expr in (m_expr, b_expr)
        ])
    except (TypeError, ValueError):
        return {name: None for name in names}
    if not np.all(np.isfinite(forward)) or np.linalg.matrix_rank(forward) < LINE_UNKNOWNS:
        return {name: None for name in names}

    jacobian = np.linalg.inv(forward)
    variances = np.diag(jacobian @ covariance @ jacobian.T)
    return {
        name: math.sqrt(var) if math.isfinite(var) and var >= 0 else None
        for name, var in zip(names, variances)
    }
