#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="${NEODON_REPO:-$HOME/AI/neodon-vpn}"
RESULTS_DIR="${QA_RESULTS_DIR:-$REPO_ROOT/qa-results}"
MODE="all"
for arg in "$@"; do
  case "$arg" in
    --static) MODE=static ;;
    --live) MODE=live ;;
    --all) MODE=all ;;
    *) echo "unknown arg: $arg" >&2; exit 2 ;;
  esac
done

rm -rf "$RESULTS_DIR"
mkdir -p "$RESULTS_DIR"
RAW="$RESULTS_DIR/raw.log"
: > "$RAW"

run_section() {
  local name="$1"; shift
  echo "== $name =="
  set +e
  "$@" 2>&1 | tee -a "$RAW"
  local rc=${PIPESTATUS[0]}
  set -e
  return "$rc"
}

pytest_rc=0
if [[ "$MODE" != live ]]; then
  run_section "L1/L2 pytest" python3 -m pytest -q "$SCRIPT_DIR/../tests" || pytest_rc=$?
fi

if [[ "$MODE" != static ]]; then
  for script in \
    "$SCRIPT_DIR/live/l3_state.sh" \
    "$SCRIPT_DIR/live/l3_servers.sh" \
    "$SCRIPT_DIR/live/l3_profiles.sh" \
    "$SCRIPT_DIR/live/l3_failures.sh" \
    "$SCRIPT_DIR/live/l3_perf.sh" \
    "$SCRIPT_DIR/live/l3_ui.sh" \
    "$SCRIPT_DIR/live/l3_regression.sh" \
    "$SCRIPT_DIR/release/l4_release.sh"; do
    set +e
    run_section "$(basename "$script")" bash "$script"
    rc=$?
    set -e
    (( rc == 0 )) || pytest_rc=$((pytest_rc+1))
  done
fi

python3 "$SCRIPT_DIR/report.py" "$RAW" "$RESULTS_DIR"
exit "$pytest_rc"
