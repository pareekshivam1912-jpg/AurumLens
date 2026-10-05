"""AurumLens Explainer and Numeric Guard package."""

from aurumlens.explain.numeric_guard import (
    NumericGuardViolationError,
    assert_numeric_guard,
    verify_numeric_guard,
)
from aurumlens.explain.explainer import (
    ExplanationResult,
    SignalExplainer,
)

__all__ = [
    "NumericGuardViolationError",
    "assert_numeric_guard",
    "verify_numeric_guard",
    "ExplanationResult",
    "SignalExplainer",
]
