#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "$0")/.." && pwd)/lib/common.sh"

if ! require_live; then
  for id in C1 C2 C3 C4 C5 C6 C7 C8 C9; do skip_case "$id" "NEODON_LIVE=1 not set"; done
  exit 0
fi

LIST_OUT="$(bash "$BACKEND_ROOT/singbox-server.sh" list 2>&1 || true)"
INDICES=($(printf '%s\n' "$LIST_OUT" | grep -oE '\[[0-9]+\]' | tr -d '[]' | sort -nu))
if [ "${#INDICES[@]}" -eq 0 ]; then
  skip_case C1 "server list did not expose numeric indices"
  for id in C2 C3 C4 C5 C6 C7 C8 C9; do skip_case "$id" "server matrix unavailable"; done
  exit 0
fi

case_C1() { ((${#INDICES[@]} >= 1)); }
case_C2() { for i in "${INDICES[@]}"; do bash "$BACKEND_ROOT/singbox-server.sh" set "$i" >/dev/null; done; }
case_C3() { bash "$BACKEND_ROOT/singbox-server.sh" set "$WORKING_SERVER" >/dev/null; }
case_C4() { [[ -f "$BACKEND_ROOT/selected-server.json" ]]; }
case_C5() { python3 - <<'PY'
import json, pathlib
p=pathlib.Path.home()/"AI/singbox/selected-server.json"
obj=json.loads(p.read_text())
assert isinstance(obj.get("server_port"), int)
PY
}
case_C6() { grep -Rqs 'ws' "$BACKEND_ROOT/config.json" "$BACKEND_ROOT/config-full.json" "$BACKEND_ROOT/config-proxy.json"; }
case_C7() { grep -Rqs 'grpc' "$BACKEND_ROOT/config.json" "$BACKEND_ROOT/config-full.json" "$BACKEND_ROOT/config-proxy.json" || return 77; }
case_C8() { grep -Rqs 'reality' "$BACKEND_ROOT/config.json" "$BACKEND_ROOT/config-full.json" "$BACKEND_ROOT/config-proxy.json" || return 77; }
case_C9() { grep -q 'selected-server.json' "$BACKEND_ROOT/singbox-server.sh"; }

run_case C1 case_C1
run_case C2 case_C2
run_case C3 case_C3
run_case C4 case_C4
run_case C5 case_C5
run_case C6 case_C6
run_case C7 case_C7
run_case C8 case_C8
run_case C9 case_C9
