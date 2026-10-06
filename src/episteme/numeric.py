"""Small, explicit numeric comparison policy for epistemic measurements."""

from __future__ import annotations

import math


# Measurements are represented as floats in the current storage model.  This
# absolute tolerance prevents binary floating-point representation noise from
# becoming a false epistemic difference.  It is deliberately small and
# deterministic; it is not an uncertainty model.
NUMERIC_ABSOLUTE_TOLERANCE = 1e-9


def numerically_equal(left: float, right: float) -> bool:
    """Return whether two finite measurements are equal within the policy tolerance."""
    if not math.isfinite(left) or not math.isfinite(right):
        raise ValueError("numeric comparison requires finite values")
    return math.isclose(
        float(left),
        float(right),
        rel_tol=0.0,
        abs_tol=NUMERIC_ABSOLUTE_TOLERANCE,
    )
