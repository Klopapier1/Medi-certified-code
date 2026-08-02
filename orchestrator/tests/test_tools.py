from pathlib import Path

from orchestrator import tools

BMI_PRODUCT = Path(__file__).resolve().parents[2] / "products" / "bmi"


def test_run_lint_on_bmi_product_is_clean():
    result = tools.run_lint(BMI_PRODUCT, "bmi")
    assert result.ok, result.combined_output


def test_run_typecheck_on_bmi_product_is_clean():
    result = tools.run_typecheck(BMI_PRODUCT, "bmi")
    assert result.ok, result.combined_output


def test_run_tests_on_bmi_product_passes():
    result = tools.run_tests(BMI_PRODUCT, "bmi")
    assert result.ok, result.combined_output
    assert "23 passed" in result.stdout


def test_run_lint_reports_real_failure(tmp_path):
    product = tmp_path / "product"
    (product / "src").mkdir(parents=True)
    (product / "src" / "widget.py").write_text("import os\n")  # unused import

    result = tools.run_lint(product, "widget")
    assert not result.ok
    assert "os" in result.combined_output
