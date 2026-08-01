# Medi-certified-code

AI orchestration framework for producing medical software code alongside the
traceable evidence package (requirements, design, tests, risk analysis,
traceability) needed to pursue certification. See `docs/mvp-scope.md` for the
full scope and rationale.

## Status

MVP pilot: one IEC 62304 Class A item (`bmi` module) taken end-to-end through
the 8-stage evidence pipeline, manually orchestrated in a single session as a
proof of concept (see `evidence/run-provenance.json`). No automated pipeline
script exists yet.

## Layout

```
requirements/   SRS.md            — software requirements, stable REQ-* IDs
design/         SDD.md            — design, traced to REQ-*
src/            bmi.py            — implementation, traced to REQ-*/design IDs
tests/          test_bmi.py       — tests mapped to REQ-*, real pytest execution
evidence/       test-report.md, static-analysis-report.md, sbom.json,
                risk-table.md, traceability-matrix.md, run-provenance.json,
                review-signoff.md — the evidence package; signoff is the
                mandatory human gate before anything here is "final"
docs/           mvp-scope.md      — MVP scope and open questions
```

## Running the pilot's checks

```
pip install -r requirements-dev.txt
python3 -m pytest tests/ -v --cov=src.bmi --cov-report=term-missing
ruff check src/
mypy --strict src/
```
