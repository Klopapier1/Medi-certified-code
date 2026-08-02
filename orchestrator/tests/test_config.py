from pathlib import Path

import pytest

from orchestrator.config import ProductSpec


def test_valid_spec():
    spec = ProductSpec(name="widget", plain_requirement="do a thing", output_dir=Path("products/widget"))
    assert spec.safety_class == "A"
    assert spec.language == "python"


def test_rejects_unsupported_safety_class():
    with pytest.raises(ValueError):
        ProductSpec(
            name="widget",
            plain_requirement="x",
            output_dir=Path("products/widget"),
            safety_class="C",
        )


def test_rejects_unsupported_language():
    with pytest.raises(ValueError):
        ProductSpec(
            name="widget",
            plain_requirement="x",
            output_dir=Path("products/widget"),
            language="rust",
        )


def test_rejects_non_identifier_name():
    with pytest.raises(ValueError):
        ProductSpec(name="not a name!", plain_requirement="x", output_dir=Path("products/x"))
