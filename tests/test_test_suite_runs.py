"""Regression guards for the cumulative test suite.

These tests guard against a cumulative test-suite regression: the canonical
``make test`` entry point must run the full suite to completion and must
discover every test module, rather than a single hardcoded file.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
MAKEFILE = REPO_ROOT / "Makefile"

# Set in the child ``make test`` environment to break recursion: the nested
# invocation runs this same file again, and those nested runs should skip the
# expensive subprocess guards (they are already executing them).
_NESTED_MARKER = "MARKET_INTEL_MAKE_TEST_NESTED"


def _make_test() -> subprocess.CompletedProcess[str]:
    env = {
        **os.environ,
        "PATH": f"{os.path.dirname(sys.executable)}{os.pathsep}{os.environ.get('PATH', '')}",
        _NESTED_MARKER: "1",
    }
    return subprocess.run(
        ["make", "test"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        env=env,
    )


def _not_nested() -> bool:
    return os.environ.get(_NESTED_MARKER) != "1"


def test_expand_runner_does_not_depend_on_venv() -> None:
    """``make test`` must be runnable even when no ``.venv`` exists yet."""
    content = MAKEFILE.read_text()
    # The target should not hard-fail on a missing venv's pytest binary; it must
    # fall back to a PATH-installed pytest so the suite is always discoverable.
    assert "PYTEST" in content, (
        "Makefile 'test' target must use a configurable test runner, not a "
        "hardcoded .venv path alone"
    )


@pytest.mark.skipif(not _not_nested(), reason="running inside nested make test")
def test_make_test_runs_full_suite_to_completion() -> None:
    """The cumulative suite must run to completion via ``make test``."""
    result = _make_test()
    assert result.returncode == 0, (
        "make test should run the full test suite successfully.\n"
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )
    assert "passed" in result.stdout or "passed" in result.stderr, (
        "make test output should report a passing run.\n"
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )


@pytest.mark.skipif(not _not_nested(), reason="running inside nested make test")
def test_make_test_discovers_every_test_module() -> None:
    """The suite must discover every test module, not only a subset.

    Each ``tests/test_*.py`` module should be collected by the test runner so a
    future ticket's new tests are never silently skipped by a hardcoded path.
    """
    test_modules = sorted(p.stem for p in (REPO_ROOT / "tests").glob("test_*.py"))
    assert test_modules, "expected at least one test module under tests/"
    result = _make_test()
    assert result.returncode == 0
    collected = f"{result.stdout}\n{result.stderr}"
    for stem in test_modules:
        assert stem in collected, (
            f"test module {stem}.py was not collected by 'make test'; the "
            f"cumulative suite does not run every test module."
        )
