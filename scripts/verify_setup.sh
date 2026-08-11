#!/usr/bin/env bash
# Deterministic setup verification for the market-intelligence agent.
# Exits 0 on success, non-zero on the first failed check.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

fail() {
    echo "verify: FAIL - $1" >&2
    exit 1
}

ok() {
    echo "verify: ok  - $1"
}

# 1. Python version >= 3.11
PY="${PYTHON:-python3}"
if ! command -v "$PY" >/dev/null 2>&1; then
    fail "python3 not found on PATH"
fi
PY_VER=$("$PY" -c 'import sys; print("%d.%d" % sys.version_info[:2])')
"$PY" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)' \
    || fail "python 3.11+ required, found $PY_VER"
ok "python version $PY_VER"

# 2. Core config files present
for f in pyproject.toml .env.example Makefile .gitignore; do
    [ -f "$ROOT/$f" ] || fail "missing required file: $f"
    ok "found $f"
done

# 3. Required env keys declared in .env.example
REQUIRED_KEYS=(
    "MARKET_INTEL_ENV"
    "MARKET_INTEL_LOG_LEVEL"
    "MARKET_INTEL_DATA_DIR"
    "MARKET_INTEL_HTTP_TIMEOUT_SECONDS"
)
for key in "${REQUIRED_KEYS[@]}"; do
    grep -qE "^${key}=" "$ROOT/.env.example" \
        || fail "required key $key not declared in .env.example"
    ok "env contract: $key"
done

# 4. Package importable
PYTHONPATH="$ROOT/src${PYTHONPATH:+:$PYTHONPATH}" \
    "$PY" -c 'import market_intel; assert market_intel.__version__' \
    || fail "package market_intel is not importable"
ok "market_intel package importable"

echo "verify: PASS"
