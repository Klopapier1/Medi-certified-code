# Software Design Description — BMI Calculator

**Item:** `bmi` module
**Traces to:** `requirements/SRS.md`

## Module

`src/bmi.py` — pure Python, no third-party dependencies, no I/O.

## Data types

```python
@dataclass(frozen=True)
class BMIResult:
    value: float       # rounded BMI, kg/m^2
    category: str      # one of: "Underweight", "Normal weight", "Overweight", "Obese"
```

Design decision: return an immutable result object (not a bare float) so category
and value travel together and can't drift apart at call sites. Traces to REQ-001, REQ-003.

## Functions

### `calculate_bmi(weight_kg: float, height_m: float) -> BMIResult`

| Design element | Behavior | Traces to |
|---|---|---|
| D-01 | Validate `weight_kg` and `height_m` are finite numbers | REQ-002 |
| D-02 | Validate both are within plausibility bounds (0.5–2.5 m, 2–500 kg) | REQ-004 |
| D-03 | Reject non-positive values (covered by D-02's lower bounds, but checked explicitly for a clearer error message) | REQ-002 |
| D-04 | Compute `weight_kg / height_m ** 2`, round to 1 decimal place | REQ-001 |
| D-05 | Map the computed value to a WHO category per the REQ-003 table | REQ-003 |
| D-06 | Return `BMIResult(value, category)` | REQ-001, REQ-003 |

### Error handling

All validation failures (D-01, D-02, D-03) raise `ValueError` with a message identifying
which input and which constraint was violated. No silent clamping or coercion — a
rejected input never produces a numeric result (REQ-002, REQ-004).

## Interfaces

- Public: `calculate_bmi`, `BMIResult`
- No module-level state, no side effects — safe to call concurrently.

## Traceability summary

| Design ID | Requirement |
|---|---|
| D-01, D-03 | REQ-002 |
| D-02 | REQ-004 |
| D-04 | REQ-001 |
| D-05 | REQ-003 |
| D-06 | REQ-001, REQ-003 |
