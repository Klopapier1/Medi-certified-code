# Preliminary Risk Analysis — `bmi` module

ISO 14971-informed hazard analysis, scoped to this software item only (not a full
product-level risk file). Software Safety Class A per `requirements/SRS.md`: by
design, this item is informational only and is not used for diagnosis, dosing, or
treatment — which bounds the severity of every row below.

| ID | Hazard | Possible cause | Potential effect | Mitigation | Residual risk |
|---|---|---|---|---|---|
| RISK-001 | Silent unit confusion (e.g., height entered in cm instead of m) | Caller passes `175` instead of `1.75` | Wildly incorrect BMI returned and potentially acted on | REQ-004 plausibility bounds reject values outside a realistic adult range | Low — caught at input, raises `ValueError` |
| RISK-002 | Division producing NaN/inf silently propagated | Non-finite input bypasses validation | Downstream code receives an unusable/nonsensical value without an obvious error | REQ-002 explicitly checks for NaN/inf before division | Low — covered by `TestREQ002InputValidation` |
| RISK-003 | Incorrect category boundary (off-by-one at 18.5/25.0/30.0) | Boundary logic error in `_categorize` | User told wrong weight category, possible false reassurance/alarm | Boundary values tested explicitly per REQ-003; categorization logic isolated in one small function with 100% test coverage | Low |
| RISK-004 | Result value/category returned out of sync (e.g., caller mutates one but not the other) | Mutable return type | Inconsistent BMI value and category displayed together | `BMIResult` is a frozen (immutable) dataclass — cannot be partially mutated after creation (D-01 in SDD) | Negligible |
| RISK-005 | Module used for a purpose beyond its intended use (e.g., clinical dosing decision) | Misuse outside SRS scope | Harm from over-reliance on an informational-only calculation | Out-of-scope statement in SRS; safety class A assignment assumes this constraint holds — **not enforced in code**, must be enforced by the calling application/product-level risk file | **Open — product-level control required, not resolvable at this module's scope** |

## Notes

- RISK-005 is flagged as the one item this module's evidence package cannot close on its
  own — it depends on how the module is integrated into a larger product, which is out of
  scope for this pilot's traceability matrix.
- This table covers the `bmi` module only. A real product-level risk management file
  (ISO 14971 full scope) would additionally cover hardware, use environment, user error,
  and cybersecurity — none of which apply to this pure-calculation pilot.
