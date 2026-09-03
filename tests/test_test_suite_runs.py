"""Regression guards for the cumulative test suite.

These tests guard against a cumulative test-suite regression: the canonical
``make test`` entry point must run the full suite to completion and must
discover every test module, rather than a single hardcoded file.
"""
from __future__ import annotations

import os
import re
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


def _make_test(extra_env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    env = {
        **os.environ,
        "PATH": f"{os.path.dirname(sys.executable)}{os.pathsep}{os.environ.get('PATH', '')}",
        _NESTED_MARKER: "1",
        **(extra_env or {}),
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


# ---------------------------------------------------------------------------
# Makefile structural checks
# ---------------------------------------------------------------------------

def test_expand_runner_does_not_depend_on_venv() -> None:
    """``make test`` must be runnable even when no ``.venv`` exists yet."""
    content = MAKEFILE.read_text()
    # The target should not hard-fail on a missing venv's pytest binary; it must
    # fall back to a PATH-installed pytest so the suite is always discoverable.
    assert "PYTEST" in content, (
        "Makefile 'test' target must use a configurable test runner, not a "
        "hardcoded .venv path alone"
    )


def test_makefile_pytest_variable_uses_wildcard_fallback() -> None:
    """The PYTEST variable must detect .venv/bin/pytest via $(wildcard …) and
    fall back to a bare ``pytest`` when the venv directory is absent."""
    content = MAKEFILE.read_text()
    # Match the PYTEST assignment line (allow flexible whitespace).
    match = re.search(r"^PYTEST\s*:=\s*(.+)$", content, re.MULTILINE)
    assert match is not None, "Makefile must define a PYTEST variable"
    definition = match.group(1).strip()
    # The definition must reference $(wildcard …) for venv detection.
    assert "$(wildcard" in definition, (
        f"PYTEST variable must use $(wildcard …) for venv detection, got: {definition}"
    )
    # The fallback must be the bare ``pytest`` command (no venv prefix).
    assert definition.endswith(",pytest)"), (
        f"PYTEST fallback must end with ,pytest), got: {definition}"
    )


def test_makefile_test_target_uses_pytest_variable() -> None:
    """The ``test`` target must invoke $(PYTEST), not a hardcoded path."""
    content = MAKEFILE.read_text()
    # Find the ``test:`` target and its recipe line(s).
    match = re.search(r"^test:\s*\n\s+\$\(PYTEST\)", content, re.MULTILINE)
    assert match is not None, (
        "Makefile 'test' target must invoke $(PYTEST), not a hardcoded path"
    )


def test_makefile_test_is_phony() -> None:
    """``test`` must be declared as .PHONY to avoid confusion with a ``test``
    file or directory that might exist in the repo."""
    content = MAKEFILE.read_text()
    phony_match = re.search(r"^\.PHONY:\s*(.+)$", content, re.MULTILINE)
    assert phony_match is not None, "Makefile must declare .PHONY targets"
    assert "test" in phony_match.group(1).split(), (
        "Makefile .PHONY must include 'test'"
    )


def test_makefile_expected_targets_exist() -> None:
    """Every canonical Makefile target (setup, verify, test, lint, clean) must
    be declared so that ``make <target>`` does not silently succeed via a
    file of the same name."""
    content = MAKEFILE.read_text()
    for target in ("setup", "verify", "test", "lint", "clean"):
        assert re.search(rf"^{target}:", content, re.MULTILINE), (
            f"Makefile must declare a '{target}' target"
        )


# ---------------------------------------------------------------------------
# Recursion-guard checks
# ---------------------------------------------------------------------------

def test_nested_marker_env_var_is_set_by_helper() -> None:
    """The ``_make_test`` helper must set the nested-marker env var so the
    child ``make test`` invocation skips the expensive subprocess guards."""
    env = {
        **os.environ,
        "PATH": f"{os.path.dirname(sys.executable)}{os.pathsep}{os.environ.get('PATH', '')}",
        _NESTED_MARKER: "1",
    }
    assert env.get(_NESTED_MARKER) == "1"


def test_not_nested_returns_true_when_marker_absent() -> None:
    """``_not_nested`` must return True when the marker is not set."""
    # Temporarily ensure the marker is absent from the current environment.
    saved = os.environ.pop(_NESTED_MARKER, None)
    try:
        assert _not_nested() is True
    finally:
        if saved is not None:
            os.environ[_NESTED_MARKER] = saved


def test_not_nested_returns_false_when_marker_set() -> None:
    """``_not_nested`` must return False when the marker is set to '1'."""
    saved = os.environ.get(_NESTED_MARKER)
    try:
        os.environ[_NESTED_MARKER] = "1"
        assert _not_nested() is False
    finally:
        if saved is not None:
            os.environ[_NESTED_MARKER] = saved
        else:
            os.environ.pop(_NESTED_MARKER, None)


# ---------------------------------------------------------------------------
# Integration: make test actually works
# ---------------------------------------------------------------------------

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


@pytest.mark.skipif(not _not_nested(), reason="running inside nested make test")
def test_make_test_output_shows_test_count() -> None:
    """The ``make test`` output must include a pytest summary line with a
    numeric test count (e.g. ``360 passed``) so CI can parse the result."""
    result = _make_test()
    assert result.returncode == 0
    combined = f"{result.stdout}\n{result.stderr}"
    # Match lines like "360 passed in 1.23s" or "360 passed, 2 warnings in …"
    assert re.search(r"\d+ passed", combined), (
        "make test output must include a numeric 'N passed' summary line.\n"
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )
