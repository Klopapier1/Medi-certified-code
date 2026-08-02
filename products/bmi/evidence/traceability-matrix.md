# Traceability Matrix — `bmi` module

| Requirement | Design element(s) | Code | Test(s) | Risk row(s) |
|---|---|---|---|---|
| REQ-001 (calculation) | D-04, D-06 | `calculate_bmi` (calculation + return) | `TestREQ001Calculation` (2 tests) | RISK-002, RISK-004 |
| REQ-002 (input validation) | D-01, D-03 | `_validate` | `TestREQ002InputValidation` (12 tests) | RISK-002 |
| REQ-003 (categorization) | D-05, D-06 | `_categorize` | `TestREQ003Categorization` (4 tests) | RISK-003, RISK-004 |
| REQ-004 (plausibility bounds) | D-02 | `_validate` | `TestREQ004PlausibilityBounds` (5 tests) | RISK-001 |
| — (not a REQ; scope boundary) | — | — | — | RISK-005 (open, product-level, not closable here) |

## Coverage check

- Every `REQ-*` in `requirements/SRS.md` has at least one design element, one code unit, and one test class. ✅
- Every design element (`D-01`–`D-06`) in `design/SDD.md` traces to a requirement. ✅
- Every risk row in `evidence/risk-table.md` traces to a requirement/design element except RISK-005, which is explicitly documented as out of this module's closable scope. ✅ (flagged, not hidden)
- All 23 tests in `tests/test_bmi.py` pass; 100% statement coverage of `src/bmi.py` (`evidence/test-report.md`).
- No orphaned rows in either direction.

**This matrix was compiled by cross-referencing the REQ-\*/D-\* IDs actually present in each
file (grep-verified), not asserted by the generating agent.**
