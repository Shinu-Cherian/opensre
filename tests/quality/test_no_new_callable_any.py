"""Quality gate: prevent untyped ``Callable[..., Any]`` seams.

Untyped callable seams reduce type safety across core agent harness ports,
harness providers, and interactive shell runtime modules. This test pins
the maximum allowed count of ``Callable[..., Any]`` occurrences under those
paths so new untyped seams fail in CI.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]

# Relative paths to check under the repository root
_TARGET_PATHS = (
    "core/agent_harness/ports.py",
    "infrastructure/harness_providers",
    "surfaces/interactive_shell/runtime",
)

# Baseline allowed count of untyped Callable[..., Any] occurrences
_BASELINE_ALLOWED_COUNT = 0


def _is_untyped_callable_any(node: ast.AST) -> bool:
    """Return True if node represents Callable[..., Any]."""
    if not isinstance(node, ast.Subscript):
        return False

    value = node.value
    if isinstance(value, ast.Name) and value.id == "Callable":
        pass
    elif isinstance(value, ast.Attribute) and value.attr == "Callable":
        pass
    else:
        return False

    slice_node = node.slice
    if isinstance(slice_node, ast.Tuple):
        elts = slice_node.elts
    else:
        elts = [slice_node]

    if len(elts) < 2:
        return False

    args_part, return_part = elts[0], elts[1]

    # Check first argument is Ellipsis (...)
    is_ellipsis = isinstance(args_part, ast.Constant) and args_part.value is Ellipsis

    # Check return type is Any
    is_any = (isinstance(return_part, ast.Name) and return_part.id == "Any") or (
        isinstance(return_part, ast.Attribute) and return_part.attr == "Any"
    )

    return is_ellipsis and is_any


def _find_callable_any_offenses(tree: ast.AST) -> list[tuple[int, str]]:
    hits: list[tuple[int, str]] = []

    class _Visitor(ast.NodeVisitor):
        def visit_Subscript(self, node: ast.Subscript) -> None:
            if _is_untyped_callable_any(node):
                hits.append((node.lineno, "Callable[..., Any]"))
            self.generic_visit(node)

    _Visitor().visit(tree)
    return hits


def _collect_python_files(rel_path: str) -> list[Path]:
    full_path = _REPO_ROOT / rel_path
    if full_path.is_file() and full_path.suffix == ".py":
        return [full_path]
    if full_path.is_dir():
        return sorted(p for p in full_path.rglob("*.py") if not p.name.startswith("test_"))
    return []


@pytest.mark.parametrize("target_path", _TARGET_PATHS)
def test_no_untyped_callable_any_seams(target_path: str) -> None:
    files = _collect_python_files(target_path)
    assert files, f"Target path {target_path} not found or contains no Python files"

    offenders: list[str] = []
    for path in files:
        source = path.read_text(encoding="utf-8")
        try:
            tree = ast.parse(source, filename=str(path))
        except SyntaxError as exc:
            offenders.append(f"{path.relative_to(_REPO_ROOT).as_posix()}: syntax error: {exc}")
            continue

        for lineno, msg in _find_callable_any_offenses(tree):
            rel_file = path.relative_to(_REPO_ROOT).as_posix()
            offenders.append(f"{rel_file}:{lineno}: untyped seam `{msg}`")

    count = len(offenders)
    assert count <= _BASELINE_ALLOWED_COUNT, (
        f"Found {count} untyped `Callable[..., Any]` occurrences under {target_path} "
        f"(baseline limit is {_BASELINE_ALLOWED_COUNT}). Type the seam or define a Protocol:\n"
        + "\n".join(offenders)
    )
