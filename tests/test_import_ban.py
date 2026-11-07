"""The demarcation guardrail — the ban the truth gate does not cover.

`assert_no_truth_access` (upstream) denies `truth`. It says nothing about
`config` (the response coefficients), `constants` (the baseline-demand
generator), `baseline` (the module that BUILDS the true baseline series) or
`assortment` (the v0.7.0 churn step: launch velocity, exit fades, sibling
cannibalization). Each is the answer key by another route, and importing any of
them from estimation code defeats blindness while the truth gate stays green —
the "structure walks out past the gate" hole. This check closes it: it AST-scans
`src/` and fails on any import of a banned module, or attribute access to one
through the package alias (`pr.assortment.churn()` imports nothing a module-name
check can see — the same hole upstream's 2026-11-04 audit #6 closed in its gate).

`baseline` and `assortment` added 2026-11-04 on the v0.7.0 re-pin (upstream
plausibility audit #6: "Lift Math's own import ban should add baseline and
assortment").

Same mechanism as the upstream gate (imports only, source-level), so it is
dependency-light and runs in the AST-only CI job. Kept demonstrated-to-fail
with permanent fixtures, like the truth gate — a guardrail never shown to fire
is not evidence.
"""

import ast
from pathlib import Path

import pytest

# The banned generator modules. `truth` is intentionally NOT here — it is the
# upstream gate's job; duplicating it would blur which check owns what (as are
# `response`/`generate`, which upstream's gate forbids since v0.7.0).
BANNED = ("config", "constants", "baseline", "assortment")
PACKAGE = "cinderhaven_promo_response"

_REPO_ROOT = Path(__file__).resolve().parents[1]
SRC = _REPO_ROOT / "src"
FIXTURES = _REPO_ROOT / "tests" / "fixtures"


def _banned_imports_in(path):
    """Every import of a BANNED module in one Python file, as (line, name)."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    hits = []
    # Names bound to the data package itself (`import cinderhaven_promo_response
    # as pr`), so `pr.<banned>` attribute access is caught too.
    package_aliases = {
        alias.asname or alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
        if alias.name == PACKAGE
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module.split(".")[-1] in BANNED:
                hits.append((node.lineno, module))
            for alias in node.names:  # from cinderhaven_promo_response import config
                if alias.name in BANNED:
                    hits.append((node.lineno, alias.name))
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".")[-1] in BANNED:
                    hits.append((node.lineno, alias.name))
        elif isinstance(node, ast.Attribute) and node.attr in BANNED:
            if isinstance(node.value, ast.Name) and node.value.id in package_aliases:
                hits.append((node.lineno, f"{node.value.id}.{node.attr}"))
    return hits


def assert_no_generator_access(root):
    """Raise AssertionError if any .py under `root` reaches a BANNED module."""
    root = Path(root)
    targets = sorted(root.rglob("*.py")) if root.is_dir() else [root]
    report = {}
    for target in targets:
        hits = _banned_imports_in(target)
        if hits:
            report[target] = hits
    if report:
        lines = ["estimation-path code reaches the generator (" + "/".join(BANNED) + "):", ""]
        for target, hits in report.items():
            lines.append(f"  {target}")
            lines.extend(f"    line {ln}: imports {name!r}" for ln, name in hits)
        lines += [
            "",
            "config holds the response coefficients; constants and baseline the",
            "baseline-demand generator; assortment the launch/exit churn. Each is",
            "the answer key. If a prior is needed, derive it from observed data or",
            "economics(), never here.",
        ]
        raise AssertionError("\n".join(lines))


def test_estimation_path_does_not_import_the_generator():
    assert_no_generator_access(SRC)


def test_check_rejects_a_module_that_imports_config():
    with pytest.raises(AssertionError):
        assert_no_generator_access(FIXTURES / "violation_imports_config.py")


def test_check_rejects_a_module_that_imports_constants():
    with pytest.raises(AssertionError):
        assert_no_generator_access(FIXTURES / "violation_imports_constants.py")


def test_check_rejects_a_module_that_imports_baseline():
    with pytest.raises(AssertionError):
        assert_no_generator_access(FIXTURES / "violation_imports_baseline.py")


def test_check_rejects_a_module_that_imports_assortment():
    with pytest.raises(AssertionError):
        assert_no_generator_access(FIXTURES / "violation_imports_assortment.py")


def test_check_rejects_attribute_access_through_the_package_alias():
    # `import cinderhaven_promo_response as pr; pr.assortment.churn()` names no
    # banned module in any import statement.
    with pytest.raises(AssertionError):
        assert_no_generator_access(FIXTURES / "violation_attribute_assortment.py")


def test_check_ignores_an_unrelated_attribute_named_baseline():
    # `result.baseline` on a non-package object is ordinary estimator code.
    assert_no_generator_access(FIXTURES / "allowed_unrelated_baseline_attr.py")
