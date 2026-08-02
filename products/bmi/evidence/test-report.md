# Test Execution Report — `bmi` module

**Command:** `python3 -m pytest tests/test_bmi.py -v --cov=src.bmi --cov-report=term-missing`
**Result:** 23 passed, 0 failed
**Coverage:** 100% (29/29 statements in `src/bmi.py`)

## Requirement → test mapping

| Requirement | Test class | Tests | Result |
|---|---|---|---|
| REQ-001 (calculation) | `TestREQ001Calculation` | 2 | PASS |
| REQ-002 (input validation) | `TestREQ002InputValidation` | 12 (parametrized) | PASS |
| REQ-003 (categorization) | `TestREQ003Categorization` | 4 (parametrized) | PASS |
| REQ-004 (plausibility bounds) | `TestREQ004PlausibilityBounds` | 5 | PASS |

## Raw output

```
============================= test session starts ==============================
platform linux -- Python 3.11.15, pytest-9.1.1, pluggy-1.6.0
collected 23 items

tests/test_bmi.py::TestREQ001Calculation::test_known_value PASSED        [  4%]
tests/test_bmi.py::TestREQ001Calculation::test_returns_bmiresult PASSED  [  8%]
tests/test_bmi.py::TestREQ002InputValidation::test_rejects_invalid_weight[0] PASSED [ 13%]
tests/test_bmi.py::TestREQ002InputValidation::test_rejects_invalid_weight[-70] PASSED [ 17%]
tests/test_bmi.py::TestREQ002InputValidation::test_rejects_invalid_weight[70] PASSED [ 21%]
tests/test_bmi.py::TestREQ002InputValidation::test_rejects_invalid_weight[None] PASSED [ 26%]
tests/test_bmi.py::TestREQ002InputValidation::test_rejects_invalid_weight[nan] PASSED [ 30%]
tests/test_bmi.py::TestREQ002InputValidation::test_rejects_invalid_weight[inf] PASSED [ 34%]
tests/test_bmi.py::TestREQ002InputValidation::test_rejects_invalid_height[0] PASSED [ 39%]
tests/test_bmi.py::TestREQ002InputValidation::test_rejects_invalid_height[-1.75] PASSED [ 43%]
tests/test_bmi.py::TestREQ002InputValidation::test_rejects_invalid_height[1.75] PASSED [ 47%]
tests/test_bmi.py::TestREQ002InputValidation::test_rejects_invalid_height[None] PASSED [ 52%]
tests/test_bmi.py::TestREQ002InputValidation::test_rejects_invalid_height[nan] PASSED [ 56%]
tests/test_bmi.py::TestREQ002InputValidation::test_rejects_invalid_height[inf] PASSED [ 60%]
tests/test_bmi.py::TestREQ003Categorization::test_category_boundaries[50-1.8-Underweight] PASSED [ 65%]
tests/test_bmi.py::TestREQ003Categorization::test_category_boundaries[70-1.75-Normal weight] PASSED [ 69%]
tests/test_bmi.py::TestREQ003Categorization::test_category_boundaries[85-1.75-Overweight] PASSED [ 73%]
tests/test_bmi.py::TestREQ003Categorization::test_category_boundaries[110-1.75-Obese] PASSED [ 78%]
tests/test_bmi.py::TestREQ004PlausibilityBounds::test_rejects_height_given_in_centimetres PASSED [ 82%]
tests/test_bmi.py::TestREQ004PlausibilityBounds::test_rejects_weight_below_bounds PASSED [ 86%]
tests/test_bmi.py::TestREQ004PlausibilityBounds::test_rejects_weight_above_bounds PASSED [ 91%]
tests/test_bmi.py::TestREQ004PlausibilityBounds::test_accepts_lower_boundary PASSED [ 95%]
tests/test_bmi.py::TestREQ004PlausibilityBounds::test_accepts_upper_boundary PASSED [100%]

================================ tests coverage ================================
Name         Stmts   Miss  Cover   Missing
------------------------------------------
src/bmi.py      29      0   100%
------------------------------------------
TOTAL           29      0   100%
============================== 23 passed in 0.12s ==============================
```
