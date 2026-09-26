#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "$0")/.." && pwd)/lib/common.sh"

IDS=(J1 J2 J3 J4)
if ! require_live; then for id in "${IDS[@]}"; do skip_case "$id" "NEODON_LIVE=1 not set"; done; exit 0; fi

measure_ms() {
  local start end
  start="$(_now_ms)"
  "$@" >/dev/null
  end="$(_now_ms)"
  echo $((end-start))
}

case_J1() { local ms; ms="$(measure_ms bash "$BACKEND_ROOT/singbox-toggle.sh" off)"; echo "INFO|J1_ms=$ms"; ((ms <= 600)); }
case_J2() { local ms; ms="$(measure_ms bash "$BACKEND_ROOT/singbox-toggle.sh" smart)"; echo "INFO|J2_ms=$ms"; ((ms <= 800)); }
case_J3() { local i ms; ms=0; for i in 1 2 3 4 5; do local x; x="$(measure_ms bash "$BACKEND_ROOT/singbox-toggle.sh" status-json)"; ms=$((ms+x)); done; ms=$((ms/5)); echo "INFO|J3_avg_ms=$ms"; ((ms <= 1500)); }
case_J4() {
  local i ok total start end
  ok=0; total=30
  for i in $(seq 1 "$total"); do
    if bash "$BACKEND_ROOT/singbox-toggle.sh" status-json | python3 -c 'import json,sys; o=json.load(sys.stdin); raise SystemExit(0 if o.get("exit_ip") else 1)'; then ok=$((ok+1)); fi
  done
  echo "INFO|J4_exit_ip_ratio=$ok/$total"
  ((ok * 100 >= total * 90))
}

for id in "${IDS[@]}"; do run_case "$id" "case_$id"; done
