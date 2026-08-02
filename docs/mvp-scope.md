# MVP Scope — AI Orchestration Framework for Certified Medical Software

> **Implementation status:** the framework described here now exists at
> `orchestrator/` (product-agnostic pipeline engine), with `products/bmi/`
> as its first pilot output. See the root `README.md` for current status
> and how to run it. This document remains the scope/rationale reference.

## 1. Framing (read this first)

No AI system can *grant* medical device certification — that's a regulatory act performed by a notified body / competent authority against a Quality Management System (QMS), based on evidence. What this framework can realistically do is:

> Given a clinical software requirement, orchestrate specialized AI agents to produce **(a)** working code and **(b)** the complete, internally-consistent evidence package a Regulatory Affairs / QA reviewer needs to pursue certification — with a mandatory human sign-off gate before anything is considered final.

The MVP targets **IEC 62304** (medical device software lifecycle), informed by **ISO 14971** (risk management), because it's the standard directly governing how software gets built and documented — not clinical trial design or hardware safety.

## 2. MVP Goal

For **one narrow, low-risk clinical software item**, prove the pipeline can go from a plain-language requirement to:
1. Traceable source code
2. A full evidence package (SRS, SDD, tests, risk table, SBOM, traceability matrix, run provenance)
3. A human-reviewable, internally consistent artifact set — with an explicit approval gate

...end-to-end, reproducibly.

## 3. MVP Boundaries

**Explicitly IN scope:**
- IEC 62304 **Class A** software item only (no injury possible if it fails — e.g., a clinical calculator, not a dosing/alarm system)
- Single target language: Python
- One requirement → one small module (e.g., a BMI or eGFR calculator) as the pilot use case
- Fully local/offline pipeline; no EHR, no PHI, no real patient data
- Human-in-the-loop approval as the final, mandatory pipeline step

**Explicitly OUT of scope (defer beyond MVP):**
- IEC 62304 Class B/C (software that could cause injury/death) — different rigor entirely
- Any claim of actual regulatory submission-readiness or notified-body acceptance
- Integration with a real QMS (e.g., Greenlight, Veeva)
- Multi-language codegen
- Clinical validation with real-world/patient data
- Cybersecurity submission artifacts (FDA premarket cyber docs, threat modeling depth)
- Usability engineering file (IEC 62366)

## 4. Pipeline (agent roles)

Sequential pipeline, each stage's output persisted and hash/version-stamped before the next stage reads it:

| # | Agent | Input | Output |
|---|-------|-------|--------|
| 1 | **Requirements Agent** | Plain-language clinical need | Structured SRS with unique IDs (`REQ-001…`) |
| 2 | **Design Agent** | SRS | Software Design Description (SDD), interfaces, traced to `REQ-*` |
| 3 | **Code Generation Agent** | SDD | Source code, each unit annotated with the `REQ-*`/design ID it implements |
| 4 | **Static Analysis Agent** | Source code | Lint/type-check/SAST report, SBOM (dependency inventory + licenses) |
| 5 | **Test Agent** | SRS + code | Unit/integration tests mapped to `REQ-*`, execution results, coverage report |
| 6 | **Risk Analysis Agent** | SRS + design | Preliminary hazard/risk table (ISO 14971-style: hazard → cause → effect → mitigation → residual risk) |
| 7 | **Evidence Compiler** | All of the above | Traceability matrix (Req↔Design↔Code↔Test↔Risk) + run provenance log (model/version/prompts/timestamps) |
| 8 | **Human Gate** | Full evidence package | Reviewer approval/rejection record — pipeline output is *draft* until this is signed |

## 5. Evidence artifacts produced (MVP)

- `requirements/SRS.md` — requirements with stable IDs
- `design/SDD.md` — design description
- `src/` — code, each function/module citing its requirement ID
- `tests/` — test suite + `results/coverage.xml`, `results/test-report.md`
- `evidence/static-analysis-report.md`, `evidence/sbom.json`
- `evidence/risk-table.md`
- `evidence/traceability-matrix.md`
- `evidence/run-provenance.json` (which model, prompt/version hashes, timestamps per stage)
- `evidence/review-signoff.md` (reviewer name, date, decision — human-authored, not AI-generated)

Git itself doubles as the audit trail: one commit per pipeline stage, so evidence has natural version history.

## 6. Success criteria for MVP

- [ ] One pilot requirement (e.g., "compute BMI from height/weight with input validation") runs through all 8 stages unattended
- [ ] Traceability matrix has zero orphaned requirements, code units, or tests (every row closes)
- [ ] Generated tests pass and cover 100% of the generated module (small surface, achievable)
- [ ] A human reviewer can, from the evidence folder alone, reconstruct *why* the code is correct and *what* risks were considered — without reading the orchestration source
- [ ] Pipeline is re-runnable and produces a fresh, consistently-structured evidence set for a second pilot requirement

## 7. Open questions (need your input before build starts)

1. **Orchestration engine**: build directly on the Claude Agent SDK (simplest, matches this environment) rather than a heavier framework (LangGraph, etc.)? Recommendation: yes for MVP — fewer moving parts.
2. **Pilot use case**: confirm a Class A calculator-style module is acceptable as the first target, or is there a specific real requirement you want piloted?
3. **Evidence format**: Markdown + JSON (human-readable, git-diffable) vs. a structured format aimed at a specific QMS tool's import schema?
4. **Who plays "Human Gate" in the MVP**: you, or a placeholder reviewer role we stub out?

## 8. Explicitly not solved by this MVP

Getting an actual device certified. That requires a real QMS, a real notified body, real risk management spanning the whole product (not just software), clinical evaluation, and organizational accountability no AI pipeline can substitute for. This MVP's job is to make the *software engineering evidence* trustworthy, complete, and fast to produce — nothing more.
