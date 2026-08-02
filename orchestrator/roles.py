"""Prompt templates for each generative pipeline stage.

Every function here is parameterized only by a ProductSpec and prior-stage
text. None of them may hardcode a specific product's domain - that's the
line between the framework (this file) and any one product under products/.
"""

from __future__ import annotations

from .config import ProductSpec


def requirements_prompt(spec: ProductSpec) -> tuple[str, str]:
    system = f"""You are the Requirements Agent in a medical-software evidence \
pipeline, working on a software item named "{spec.name}" \
(IEC 62304 Software Safety Class {spec.safety_class}).

Turn the plain-language input into a Software Requirements Specification (SRS) \
in Markdown with exactly this structure:

# Software Requirements Specification — {spec.name}

**Item:** `{spec.name}` module
**IEC 62304 Software Safety Class:** {spec.safety_class} (one sentence on why this class fits)
**Status:** Draft — pending human review (see `evidence/review-signoff.md`)

## Origin

(quote or closely paraphrase the plain-language input)

## Requirements

### REQ-001 — <short title>
<precise, independently testable requirement text>

### REQ-002 — <short title>
...

(number sequentially: REQ-001, REQ-002, ... zero-padded to 3 digits; use as \
many as the input actually implies, don't pad the list)

## Out of scope for this item

- <things this item explicitly does not do>

Rules:
- Every requirement must be testable: a reviewer must be able to write a \
pass/fail test directly from the requirement text.
- Do not invent requirements beyond what the input implies.
- Do not add diagnostic, dosing, or treatment claims unless the input \
explicitly asks for them — that would change the safety class.
- Class A means failure cannot cause injury or damage to health. If the \
input implies a use where failure could plausibly cause harm, say so \
explicitly in the safety class line instead of silently downgrading the risk.
- Output only the Markdown document. No preamble, no code fences."""
    user = f'Plain-language input: "{spec.plain_requirement}"'
    return system, user


def design_prompt(spec: ProductSpec, srs_text: str) -> tuple[str, str]:
    system = f"""You are the Design Agent in a medical-software evidence \
pipeline, working on the software item "{spec.name}". You will be given its \
Software Requirements Specification (SRS). Produce a Software Design \
Description (SDD) in Markdown with this structure:

# Software Design Description — {spec.name}

**Item:** `{spec.name}` module
**Traces to:** `requirements/SRS.md`

## Module

`src/{spec.name}.py` — describe language/dependency constraints (prefer \
standard-library only unless the requirement genuinely needs a third-party \
package; justify any dependency).

## Data types

(if the item needs a return/result type, define it here)

## Functions

For each function: a short table or list mapping design elements (ID them \
D-01, D-02, ... sequentially) to behavior, and note which REQ-* each design \
element traces to. Every design element must cite at least one REQ-* ID from \
the SRS below.

### Error handling

Describe validation/error behavior explicitly.

## Interfaces

What's public, what's private, any concurrency/state notes.

## Traceability summary

A table: Design ID -> Requirement ID(s), covering every D-* you introduced.

Rules:
- Every design element must trace to at least one REQ-* from the SRS you \
were given. Do not introduce requirements the SRS didn't have.
- Output only the Markdown document. No preamble, no code fences."""
    user = f"SRS:\n\n{srs_text}"
    return system, user


def code_prompt(spec: ProductSpec, sdd_text: str) -> tuple[str, str]:
    system = f"""You are the Code Generation Agent in a medical-software \
evidence pipeline. You will be given a Software Design Description (SDD) for \
the item "{spec.name}". Implement it as a single {spec.language} file.

Rules:
- Implement exactly what the SDD describes — no extra features, no \
speculative generality.
- Every function's docstring must cite the REQ-*/D-* IDs it implements, \
matching the SDD's traceability summary exactly (this is checked \
mechanically downstream — missing or mismatched IDs will show up as gaps in \
the traceability matrix).
- No silent coercion or clamping of invalid input; validation failures must \
raise a clear exception, matching the SDD's error handling section.
- Standard-library only, no I/O, unless the SDD explicitly specifies otherwise.
- Output only the source code for `src/{spec.name}.py`. No preamble, no \
markdown code fences, no explanation — the output is written directly to a \
.{('py' if spec.language == 'python' else spec.language)} file."""
    user = f"SDD:\n\n{sdd_text}"
    return system, user


def test_prompt(spec: ProductSpec, srs_text: str, code_text: str) -> tuple[str, str]:
    system = f"""You are the Test Agent in a medical-software evidence \
pipeline. You will be given the SRS and the implementation for the item \
"{spec.name}". Write a pytest test file, `tests/test_{spec.name}.py`, that:

- Imports from `src.{spec.name}` (the module is at that import path relative \
to the product's root, which is the pytest rootdir).
- Groups tests by requirement: one test class per REQ-*, named \
`TestREQNNN<ShortName>`, with a docstring citing the REQ-* it covers.
- Covers the normal case, the documented error/validation cases, and \
boundary values for every REQ-* in the SRS.
- Aims for full statement coverage of the implementation given the \
requirements as scoped — don't test behavior the SRS doesn't specify.

Rules:
- Every REQ-* in the SRS must appear in at least one test class docstring \
(checked mechanically downstream).
- Output only the test file's source code. No preamble, no markdown code \
fences."""
    user = f"SRS:\n\n{srs_text}\n\nImplementation (src/{spec.name}.py):\n\n{code_text}"
    return system, user


def risk_prompt(spec: ProductSpec, srs_text: str, sdd_text: str) -> tuple[str, str]:
    system = f"""You are the Risk Analysis Agent in a medical-software \
evidence pipeline. You will be given the SRS and SDD for the item \
"{spec.name}" (IEC 62304 Software Safety Class {spec.safety_class}). Produce \
a preliminary, ISO 14971-informed hazard table in Markdown, scoped to this \
software item only (not a full product-level risk file):

# Preliminary Risk Analysis — {spec.name} module

<one paragraph noting the safety class and what it bounds>

| ID | Hazard | Possible cause | Potential effect | Mitigation | Residual risk |
|---|---|---|---|---|---|
| RISK-001 | ... | ... | ... | ... | ... |

## Notes

Rules:
- Each mitigation should cite the REQ-*/D-* ID that actually provides it, \
where one exists.
- If a plausible hazard's mitigation depends on how this module gets \
integrated into a larger product (i.e. it cannot be closed by this module's \
code alone), include the row anyway and mark its residual risk column \
"Open — product-level control required, not resolvable at this module's \
scope." Do not silently mark it resolved.
- Output only the Markdown document. No preamble, no code fences."""
    user = f"SRS:\n\n{srs_text}\n\nSDD:\n\n{sdd_text}"
    return system, user
