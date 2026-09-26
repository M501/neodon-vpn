#!/usr/bin/env bash
set -u

QA_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO_ROOT="${NEODON_REPO:-$HOME/AI/neodon-vpn}"
BACKEND_ROOT="${NEODON_BACKEND:-$HOME/AI/singbox}"
RESULTS_DIR="${QA_RESULTS_DIR:-$REPO_ROOT/qa-results}"
WORKING_SERVER="${NEODON_WORKING_SERVER:-0}"

mkdir -p "$RESULTS_DIR"

_now_ms() { date +%s%3N; }

_emit() {
    local case_id="$1" status="$2" start="$3" details="${4:-}"
    local end ms
    end="$(_now_ms)"
    ms=$((end-start))
    details="${details//$'\n'/ }"
    printf 'CASE|%s|%s|%s|%s\n' "$case_id" "$status" "$ms" "$details"
}

run_case() {
    local id="$1"; shift
    local start rc
    start="$(_now_ms)"
    set +e
    "$@"
    rc=$?
    set -e
    if [ "$rc" -eq 0 ]; then
        _emit "$id" PASS "$start" ""
    elif [ "$rc" -eq 77 ]; then
        _emit "$id" SKIP "$start" "explicit prerequisite/impact gate"
    else
        _emit "$id" FAIL "$start" "exit=$rc"
    fi
    return 0
}

skip_case() {
    local id="$1"; shift
    local start="$(_now_ms)"
    _emit "$id" SKIP "$start" "$*"
}

require_live() {
    [ "${NEODON_LIVE:-0}" = 1 ] || return 1
}

require_disruptive() {
    [ "${NEODON_ALLOW_DISRUPTIVE:-0}" = 1 ] || return 1
}

require_firewall() {
    [ "${NEODON_ALLOW_FIREWALL:-0}" = 1 ] || return 1
}

require_ui_input() {
    [ "${NEODON_ALLOW_UI_INPUT:-0}" = 1 ] || return 1
}

status_json() {
    bash "$BACKEND_ROOT/singbox-toggle.sh" status-json
}

json_field() {
    local field="$1"
    python3 - "$field" <<'PY'
import json, sys
field = sys.argv[1]
obj = json.loads(sys.stdin.read())
value = obj.get(field)
print("null" if value is None else value)
PY
}

canonical() {
    python3 "$BACKEND_ROOT/apply-profile.py" default || return 1
    bash "$BACKEND_ROOT/singbox-toggle.sh" smart || return 1
    bash "$BACKEND_ROOT/singbox-server.sh" set "$WORKING_SERVER" || return 1
    return 0
}

cleanup_canonical() {
    set +e
    canonical
    local rc=$?
    if [ "$rc" -eq 0 ]; then
        echo "CLEANUP|PASS"
    else
        echo "CLEANUP|FAIL|exit=$rc"
    fi
    set -e
    return "$rc"
}

on_exit_cleanup() {
    cleanup_canonical || true
}

trap on_exit_cleanup EXIT INT TERM
