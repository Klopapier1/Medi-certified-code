"""CLI entrypoint: python -m orchestrator.cli --name ... --requirement ... --output-dir ...

Reads ANTHROPIC_API_KEY from the environment (see orchestrator/client.py).
If a `.env` file exists in the working directory and python-dotenv is
installed, it's loaded automatically so ANTHROPIC_API_KEY/ORCHESTRATOR_MODEL
can live there instead of the shell environment. Both are optional - this
never overrides variables already set in the environment.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from .config import ProductSpec
from .pipeline import Pipeline

try:
    from dotenv import load_dotenv

    load_dotenv()  # no-op if there's no .env file; never overrides existing env vars
except ImportError:
    pass


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run the medical-code evidence pipeline for one software item.",
    )
    parser.add_argument(
        "--name",
        required=True,
        help="Short identifier for the item, e.g. 'bmi' (becomes the module and test file name)",
    )
    parser.add_argument(
        "--requirement",
        required=True,
        help="Plain-language description of what the item should do",
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        type=Path,
        help="Where to write the product's artifacts, e.g. products/bmi",
    )
    parser.add_argument(
        "--safety-class",
        default="A",
        help="IEC 62304 safety class (MVP only supports 'A')",
    )
    parser.add_argument(
        "--model",
        default=os.environ.get("ORCHESTRATOR_MODEL", "claude-sonnet-5"),
        help="Claude model id to use for the generative stages "
        "(default: $ORCHESTRATOR_MODEL, falling back to 'claude-sonnet-5')",
    )
    args = parser.parse_args(argv)

    spec = ProductSpec(
        name=args.name,
        plain_requirement=args.requirement,
        output_dir=args.output_dir,
        safety_class=args.safety_class,
        model=args.model,
    )

    pipeline = Pipeline(spec)
    pipeline.run()

    print(f"Done. Evidence package written to {spec.output_dir}")
    print(
        "Reminder: nothing here is final until a human completes "
        f"{spec.output_dir}/evidence/review-signoff.md"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
