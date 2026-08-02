# Demo input

A ready-to-run example input for the pipeline, so a fresh run can be tried
without first having to write your own requirement.

## What's here

```
demo/
└── bmi/
    ├── input.env    # the demo's ProductSpec fields
    └── run.sh        # loads input.env and runs the pipeline
```

`bmi/input.env` holds one demo item's input, using the same fields as the
[Input](../README.md#input) table in the root README (`orchestrator/config.py::ProductSpec`):

| `input.env` key | `ProductSpec` field | CLI flag |
|---|---|---|
| `NAME` | `name` | `--name` |
| `REQUIREMENT` | `plain_requirement` | `--requirement` |
| `OUTPUT_DIR` | `output_dir` | `--output-dir` |
| `SAFETY_CLASS` | `safety_class` | `--safety-class` |

The demo writes to `products/bmi-demo/` rather than `products/bmi/`, so it
doesn't overwrite the existing hand-orchestrated BMI pilot.

## Running it

```bash
pip install -r orchestrator/requirements.txt
pip install -r requirements-dev.txt
cp .env.example .env   # then fill in ANTHROPIC_API_KEY
./demo/bmi/run.sh
```

This runs all 8 pipeline stages and writes the evidence package to
`products/bmi-demo/`. As with any run, the package stays a draft until a
human fills in `products/bmi-demo/evidence/review-signoff.md`.

## Adding another demo

Copy `bmi/` to a new subfolder, edit `input.env` (a new `NAME`, a different
`REQUIREMENT`, and an `OUTPUT_DIR` that doesn't collide with an existing
product), and run its `run.sh`.
