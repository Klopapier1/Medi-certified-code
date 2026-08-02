"""BMI calculation module.

Traces to requirements/SRS.md and design/SDD.md.
Software Safety Class: A (IEC 62304) — informational only, not for
diagnosis, dosing, or treatment decisions.
"""

from dataclasses import dataclass

_HEIGHT_M_MIN, _HEIGHT_M_MAX = 0.5, 2.5
_WEIGHT_KG_MIN, _WEIGHT_KG_MAX = 2.0, 500.0

_CATEGORY_THRESHOLDS = (
    (18.5, "Underweight"),
    (25.0, "Normal weight"),
    (30.0, "Overweight"),
)
_OBESE_CATEGORY = "Obese"


@dataclass(frozen=True)
class BMIResult:
    """REQ-001, REQ-003: computed value and its WHO category, kept together."""

    value: float
    category: str


def _validate(name: str, value: float, low: float, high: float) -> None:
    """D-01, D-02, D-03 (REQ-002, REQ-004): reject invalid/implausible input."""
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValueError(f"{name} must be a number, got {type(value).__name__}")
    if value != value or value in (float("inf"), float("-inf")):  # NaN / inf
        raise ValueError(f"{name} must be finite, got {value}")
    if value <= 0:
        raise ValueError(f"{name} must be positive, got {value}")
    if not (low <= value <= high):
        raise ValueError(
            f"{name}={value} is outside the plausible adult range [{low}, {high}]"
        )


def _categorize(value: float) -> str:
    """D-05 (REQ-003)."""
    for threshold, category in _CATEGORY_THRESHOLDS:
        if value < threshold:
            return category
    return _OBESE_CATEGORY


def calculate_bmi(weight_kg: float, height_m: float) -> BMIResult:
    """Compute BMI and its WHO category.

    Traces to REQ-001 (calculation), REQ-002 (input validation),
    REQ-003 (categorization), REQ-004 (plausibility bounds).

    Raises:
        ValueError: if weight_kg or height_m is non-numeric, non-positive,
            or outside the plausible adult range.
    """
    _validate("height_m", height_m, _HEIGHT_M_MIN, _HEIGHT_M_MAX)
    _validate("weight_kg", weight_kg, _WEIGHT_KG_MIN, _WEIGHT_KG_MAX)

    value = round(weight_kg / (height_m**2), 1)
    category = _categorize(value)
    return BMIResult(value=value, category=category)
