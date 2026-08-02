# Phase 2 — Certification Knowledge Graph (Living Traceability)

Reference for the data model behind `orchestrator/ckg.py`, so Phase 3/4 work
(multi-agent review, versioned/frozen graphs) can extend this vocabulary
instead of renaming it. See the root
[`Certification_by_Construction_Implementation_Plan_v2.md`](../../Certification_by_Construction_Implementation_Plan_v2.md)
for the full 8-phase roadmap this fits into.

## What changed vs. Phase 1

Phase 1's traceability matrix (`orchestrator/evidence.py`) was a flat regex
scan: `REQ-\d+` grep'd across five fixed file paths, diffed into a
presence/absence table. Phase 2 replaces the *internal representation* with
an explicit graph (`orchestrator/ckg.py`) while keeping the matrix's output
**byte-identical** — `evidence.build_traceability_matrix()` now builds a
graph and renders the matrix from it, but nothing about the artifact
generation stages (SRS/SDD/code, still produced by `roles.py` LLM prompts)
changed. See the `CKG` class docstring in `ckg.py` for why the matrix
rendering deliberately still relies on a whole-file `coverage` scan rather
than only the structured graph edges.

## Node types

| Node type | Parsed from | Phase 4 equivalent |
|---|---|---|
| `Requirement` | `### REQ-NNN — Title` headings in `requirements/SRS.md` | `Requirement` |
| `DesignElement` | `\| D-NN \| ... \| REQ-... \|` table rows in `design/SDD.md` | `Design Decision` |
| `CodeArtifact` | one node per `src/<module>.py` | `Component` |
| `TestCase` | one node per `class TestREQ...` in `tests/test_<module>.py` | `Test` |
| `RiskRow` | `\| RISK-NNN \| ... \|` rows in `evidence/risk-table.md` | `Hazard` + `Risk Control` (kept merged; splitting is Phase 4 work) |
| `EvidenceArtifact` | one node per generated evidence file (static-analysis-report.md, test-report.md, run-provenance.json, sbom.json, review-signoff.md) | `Evidence` |

Not modeled yet (no source data exists): `Interface`, `Constraint`,
`Verification Result` as a distinct node.

## Edge types

All edges are stored **dependent → depended-upon**, so a single traversal
rule (`CKG.downstream_impact`, which walks incoming edges via `edges_to()`)
works uniformly for every edge type:

- `IMPLEMENTS` — `DesignElement -> Requirement`, `CodeArtifact -> Requirement`
- `VERIFIED_BY` — `TestCase -> Requirement` (note: this is the reverse of the
  natural-language reading "Requirement is verified by Test" — it's stored
  this way specifically so a test is correctly reported as impacted when its
  requirement changes; render it the other way around when displaying it)
- `MITIGATES` — `RiskRow -> Requirement` or `RiskRow -> DesignElement`
  (whichever the mitigation text actually cites — e.g. the BMI pilot's
  RISK-004 mitigation cites `D-01`, not a requirement, directly)

Reserved but not yet populated (named now per the Phase 4 vocabulary so nothing
needs renaming later): `DEPENDS_ON`, `SATISFIES`, `GENERATED_FROM`.

## Persistence

One `evidence/ckg.json` per product (`schemaVersion: 1`), written by
`ckg.write_graph()` as part of `Pipeline._compile_evidence`. Plain dataclasses
+ JSON, not `networkx` — Phase 2's graphs are a few dozen nodes per product,
which doesn't justify a new dependency. `CKG`'s public surface (attributed
nodes/edges, `edges_to`/`edges_from` traversal) is deliberately shaped like
`networkx.DiGraph` so that if a later phase's cross-product `DEPENDS_ON`
graphs or contradiction detection need real graph algorithms, swapping the
internal representation is mechanical rather than a rewrite of every call
site.

## Deliverables (`orchestrator/ckg_cli.py`, `orchestrator/incremental.py`)

- **Change impact analysis** — `python -m orchestrator.ckg_cli impact --product-dir products/bmi --module bmi --node REQ-002` lists every node transitively dependent on the given node.
- **Graph explorer** — `explore` (full dump, `--json`/`--dot` for machine/visual consumption) and `show --node <id>` (one node's edges in both directions). CLI-only for now; no web explorer exists yet.
- **Incremental regeneration** — `regenerate --changed REQ-002,D-04` re-runs only the pipeline stages downstream of the changed nodes (see `incremental.impacted_stages`) instead of the full 8-stage `Pipeline.run()`.
