#!/usr/bin/env bash
# Demo run: BMI calculator through the full 8-stage pipeline.
# Requires ANTHROPIC_API_KEY (see .env.example) - the LLM-driven stages
# fail fast without it.
set -euo pipefail

cd "$(dirname "$0")/../.."

set -a
source demo/bmi/input.env
set +a

python3 -m orchestrator.cli \
  --name "$NAME" \
  --requirement "$REQUIREMENT" \
  --output-dir "$OUTPUT_DIR" \
  --safety-class "$SAFETY_CLASS"
