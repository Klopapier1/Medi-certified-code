"""Tests for src/bmi.py, mapped to requirements/SRS.md."""

import pytest

from src.bmi import BMIResult, calculate_bmi


class TestREQ001Calculation:
    """REQ-001: BMI = weight_kg / height_m ** 2."""

    def test_known_value(self):
        result = calculate_bmi(weight_kg=70, height_m=1.75)
        assert result.value == pytest.approx(22.9, abs=0.05)

    def test_returns_bmiresult(self):
        result = calculate_bmi(weight_kg=70, height_m=1.75)
        assert isinstance(result, BMIResult)


class TestREQ002InputValidation:
    """REQ-002: reject non-positive / non-numeric input."""

    @pytest.mark.parametrize("weight", [0, -70, "70", None, float("nan"), float("inf")])
    def test_rejects_invalid_weight(self, weight):
        with pytest.raises(ValueError):
            calculate_bmi(weight_kg=weight, height_m=1.75)

    @pytest.mark.parametrize("height", [0, -1.75, "1.75", None, float("nan"), float("inf")])
    def test_rejects_invalid_height(self, height):
        with pytest.raises(ValueError):
            calculate_bmi(weight_kg=70, height_m=height)


class TestREQ003Categorization:
    """REQ-003: WHO category boundaries."""

    @pytest.mark.parametrize(
        "weight_kg,height_m,expected_category",
        [
            (50, 1.80, "Underweight"),   # BMI ~15.4
            (70, 1.75, "Normal weight"), # BMI ~22.9
            (85, 1.75, "Overweight"),    # BMI ~27.8
            (110, 1.75, "Obese"),        # BMI ~35.9
        ],
    )
    def test_category_boundaries(self, weight_kg, height_m, expected_category):
        result = calculate_bmi(weight_kg=weight_kg, height_m=height_m)
        assert result.category == expected_category


class TestREQ004PlausibilityBounds:
    """REQ-004: reject implausible / unit-confused input."""

    def test_rejects_height_given_in_centimetres(self):
        with pytest.raises(ValueError):
            calculate_bmi(weight_kg=70, height_m=175)  # 175 m is not a human

    def test_rejects_weight_below_bounds(self):
        with pytest.raises(ValueError):
            calculate_bmi(weight_kg=1, height_m=1.75)

    def test_rejects_weight_above_bounds(self):
        with pytest.raises(ValueError):
            calculate_bmi(weight_kg=600, height_m=1.75)

    def test_accepts_lower_boundary(self):
        calculate_bmi(weight_kg=2, height_m=0.5)  # should not raise

    def test_accepts_upper_boundary(self):
        calculate_bmi(weight_kg=500, height_m=2.5)  # should not raise
