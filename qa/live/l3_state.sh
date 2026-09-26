#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "$0")/.." && pwd)/lib/common.sh"

if ! require_live; then
  for id in A1 A2 A3 A4 A5 A6 A7 B1 B2 B3 B4 B5 D1 D2 D3 D4 D5 D6 D7; do skip_case "$id" "NEODON_LIVE=1 not set"; done
  exit 0
fi

case_A1() {
  local j; j="$(status_json)"
  python3 -c 'import json,sys; o=json.loads(sys.argv[1]); assert o["actual_state"] in {"OFF","STARTING","TRANSITIONING","CONNECTING","CONNECTED","DEGRADED","FAILED","LOCKED","STOPPING"}' "$j"
}
case_A2() { bash "$BACKEND_ROOT/singbox-toggle.sh" off >/dev/null; [[ "$(python3 -c 'import json,sys; print(json.loads(sys.argv[1])["desired_mode"])' "$(status_json)")" == off ]]; }
case_A3() { bash "$BACKEND_ROOT/singbox-toggle.sh" smart >/dev/null; [[ "$(python3 -c 'import json,sys; print(json.loads(sys.argv[1])["desired_mode"])' "$(status_json)")" == smart ]]; }
case_A4() { bash "$BACKEND_ROOT/singbox-toggle.sh" proxy >/dev/null; [[ "$(python3 -c 'import json,sys; print(json.loads(sys.argv[1])["desired_mode"])' "$(status_json)")" == proxy ]]; }
case_A5() { bash "$BACKEND_ROOT/singbox-toggle.sh" smart >/dev/null; bash "$BACKEND_ROOT/singbox-toggle.sh" smart >/dev/null; }
case_A6() { bash "$BACKEND_ROOT/singbox-toggle.sh" off >/dev/null; bash "$BACKEND_ROOT/singbox-toggle.sh" smart >/dev/null; bash "$BACKEND_ROOT/singbox-toggle.sh" off >/dev/null; bash "$BACKEND_ROOT/singbox-toggle.sh" smart >/dev/null; }
case_A7() { for _ in 1 2 3; do bash "$BACKEND_ROOT/singbox-toggle.sh" status-json >/dev/null; done; }

case_B1() { bash "$BACKEND_ROOT/singbox-toggle.sh" off >/dev/null; bash "$BACKEND_ROOT/singbox-toggle.sh" proxy >/dev/null; }
case_B2() { bash "$BACKEND_ROOT/singbox-toggle.sh" proxy >/dev/null; bash "$BACKEND_ROOT/singbox-toggle.sh" smart >/dev/null; }
case_B3() { bash "$BACKEND_ROOT/singbox-toggle.sh" smart >/dev/null; bash "$BACKEND_ROOT/singbox-toggle.sh" full >/dev/null; }
case_B4() { bash "$BACKEND_ROOT/singbox-toggle.sh" full >/dev/null; bash "$BACKEND_ROOT/singbox-toggle.sh" smart >/dev/null; }
case_B5() { bash "$BACKEND_ROOT/singbox-toggle.sh" smart >/dev/null; }

case_D1() { status_json | python3 -c 'import json,sys; o=json.load(sys.stdin); assert set(o) >= {"desired_mode","actual_state","service","service_state","firewall_rules","tun0","exit_ip","server_tag","latency_ms","watchdog_status","consecutive_failures","next_retry"}' ; }
case_D2() { status_json | python3 -c 'import json,sys,ipaddress; o=json.load(sys.stdin); ip=o.get("exit_ip"); assert ip is None or ipaddress.ip_address(ip)' ; }
case_D3() { local j; j="$(status_json)"; python3 -c 'import json,sys; o=json.loads(sys.argv[1]); assert o["latency_ms"] is None or o["latency_ms"] >= 0' "$j"; }
case_D4() { local n=0; for _ in 1 2; do j="$(status_json)"; s="$(python3 -c 'import json,sys; print(json.loads(sys.argv[1])["actual_state"])' "$j")"; [[ "$s" == "CONNECTED" || "$s" == "DEGRADED" || "$s" == "TRANSITIONING" || "$s" == "CONNECTING" ]]; n=$((n+1)); done; ((n==2)); }
case_D5() { local a b; a="$(status_json)"; sleep 0.5; b="$(status_json)"; [[ -n "$a" && -n "$b" ]]; }
case_D6() { status_json >/dev/null; }
case_D7() { status_json >/dev/null; }

for item in A1 A2 A3 A4 A5 A6 A7 B1 B2 B3 B4 B5 D1 D2 D3 D4 D5 D6 D7; do
  run_case "$item" "case_$item"
done
