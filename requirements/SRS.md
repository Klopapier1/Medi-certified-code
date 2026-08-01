# Software Requirements Specification — BMI Calculator

**Item:** `bmi` module
**IEC 62304 Software Safety Class:** A (no injury or damage to health possible from failure — informational/wellness calculation only, not used for diagnosis, dosing, or treatment decisions)
**Status:** Draft — pending human review (see `evidence/review-signoff.md`)

## Origin

Plain-language input: *"Calculate BMI from height and weight."*

## Requirements

### REQ-001 — BMI calculation
The system shall compute Body Mass Index from a person's weight in kilograms and height in metres using the formula:

```
BMI = weight_kg / (height_m ** 2)
```

### REQ-002 — Input validation (non-positive / non-numeric)
The system shall reject weight or height values that are not positive, finite numbers, raising a descriptive error rather than returning a numeric result computed from invalid input.

### REQ-003 — BMI categorization
The system shall classify a computed BMI value into one of the standard WHO adult categories:

| Category | BMI range (kg/m²) |
|---|---|
| Underweight | < 18.5 |
| Normal weight | 18.5 – 24.9 |
| Overweight | 25.0 – 29.9 |
| Obese | ≥ 30.0 |

### REQ-004 — Plausibility bounds (unit-confusion guard)
The system shall reject height and weight values outside physiologically plausible bounds for an adult human (height: 0.5 m – 2.5 m; weight: 2 kg – 500 kg), to catch unit-confusion errors (e.g., height entered in centimetres instead of metres) rather than silently producing a nonsensical BMI.

## Out of scope for this item

- Pediatric BMI percentile calculation
- Any diagnostic, dosing, or treatment recommendation derived from the BMI value
- Persistence, UI, or network I/O — this is a pure calculation module
