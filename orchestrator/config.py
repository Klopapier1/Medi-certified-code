"""Product-agnostic pipeline configuration.

Everything specific to one software item (its domain, its clinical intent)
lives in a ProductSpec instance and in the artifacts the pipeline writes to
its output_dir. Nothing elsewhere in this package should ever reference a
specific product by name.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

# IEC 62304 Class B/C need risk-based branching (e.g. independent review
# stages, deeper hazard analysis) this pipeline doesn't implement yet.
# See docs/mvp-scope.md for the MVP boundary.
SUPPORTED_SAFETY_CLASSES = ("A",)
SUPPORTED_LANGUAGES = ("python",)


@dataclass(frozen=True)
class ProductSpec:
    """Describes one software item to run through the evidence pipeline."""

    name: str
    plain_requirement: str
    output_dir: Path
    safety_class: str = "A"
    language: str = "python"
    model: str = "claude-sonnet-5"

    def __post_init__(self) -> None:
        if self.safety_class not in SUPPORTED_SAFETY_CLASSES:
            raise ValueError(
                f"safety_class={self.safety_class!r} is not supported yet; "
                f"MVP only supports {SUPPORTED_SAFETY_CLASSES} (see docs/mvp-scope.md)"
            )
        if self.language not in SUPPORTED_LANGUAGES:
            raise ValueError(
                f"language={self.language!r} is not supported yet; "
                f"MVP only supports {SUPPORTED_LANGUAGES}"
            )
        if not self.name.isidentifier():
            raise ValueError(
                f"name={self.name!r} must be a valid Python identifier "
                "(it becomes the module and test file name)"
            )
