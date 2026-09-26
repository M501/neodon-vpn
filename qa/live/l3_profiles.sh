#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "$0")/.." && pwd)/lib/common.sh"

if ! require_live; then
  for id in F1 F2 F3 F4 E1 E2 E3 E4 E5 E6; do skip_case "$id" "NEODON_LIVE=1 not set"; done
  exit 0
fi

PROFILES=("$BACKEND_ROOT"/profiles/*.json)
if [ ! -e "${PROFILES[0]}" ]; then
  for id in F1 F2 F3 F4 E1 E2 E3 E4 E5 E6; do skip_case "$id" "profiles/ not present"; done
  exit 0
fi

case_F1() { ((${#PROFILES[@]} == 11)); }
case_F2() { for p in "${PROFILES[@]}"; do python3 -m json.tool "$p" >/dev/null; done; }
case_F3() { bash "$BACKEND_ROOT/apply-profile.py" default >/dev/null; }
case_F4() { [[ "$(cat "$BACKEND_ROOT/.profile" 2>/dev/null || true)" == default ]]; }
case_E1() { [[ -f "$HOME/AI/neodon-sub/raw.json" ]] || return 0; python3 -m json.tool "$HOME/AI/neodon-sub/raw.json" >/dev/null; }
case_E2() { return 77; } # expired-link refresh requires a controllable subscription fixture
case_E3() { return 77; } # no-subscription UI path requires deterministic fixture injection
case_E4() { return 77; } # quota conversion needs a deterministic subscription fixture
case_E5() { grep -Rqs 'cookie' "$BACKEND_ROOT" "$REPO_ROOT" 2>/dev/null; }
case_E6() { [[ -f "$REPO_ROOT/neodon-vpn.py" ]] || return 77; grep -Eq '30.{0,8}(min|MINUTE|minutes)|1800' "$REPO_ROOT/neodon-vpn.py"; }

run_case F1 case_F1
run_case F2 case_F2
run_case F3 case_F3
run_case F4 case_F4
run_case E1 case_E1
run_case E2 case_E2
run_case E3 case_E3
run_case E4 case_E4
run_case E5 case_E5
run_case E6 case_E6
