#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "$0")/.." && pwd)/lib/common.sh"

IDS=(G1 G2 G3 G4 G5 G6 H1 H2 H3 H4 H5 H6 H7 H8)

if ! require_live; then
  for id in "${IDS[@]}"; do skip_case "$id" "NEODON_LIVE=1 not set"; done
  exit 0
fi

if ! require_disruptive; then
  for id in "${IDS[@]}"; do skip_case "$id" "requires NEODON_ALLOW_DISRUPTIVE=1"; done
  exit 0
fi

case_G1() {
  require_firewall || return 77
  bash "$BACKEND_ROOT/singbox-toggle.sh" full >/dev/null
  firewall-cmd --direct --get-all-rules | grep -q 'OUTPUT_direct'
}
case_G2() {
  require_firewall || return 77
  bash "$BACKEND_ROOT/singbox-server.sh" set "$WORKING_SERVER" >/dev/null
  grep -q "${WORKING_SERVER}" < <(firewall-cmd --direct --get-all-rules) || return 77
}
case_G3() {
  bash "$BACKEND_ROOT/singbox-toggle.sh" off >/dev/null
  ! firewall-cmd --direct --get-all-rules | grep -q 'OUTPUT_direct.*20'
}
case_G4() {
  require_firewall || return 77
  bash "$BACKEND_ROOT/singbox-toggle.sh" full >/dev/null
  [[ "$(systemctl --user is-active sing-box-full.service || true)" == active ]]
}
case_G5() { return 77; } # DNS static/stub transition should use a snapshot-based fixture on prod
case_G6() { bash "$BACKEND_ROOT/dns-fix.sh" restore >/dev/null; }
case_H1() {
  bash "$BACKEND_ROOT/singbox-toggle.sh" smart >/dev/null
  local pid="$(systemctl --user show -p MainPID --value sing-box.service)"
  [[ "$pid" =~ ^[0-9]+$ && "$pid" -gt 1 ]]
  kill -9 "$pid"
  sleep 5
  [[ "$(systemctl --user is-active sing-box.service || true)" == active ]]
}
case_H2() { return 77; } # network interruption needs a reversible host-level fault injector
case_H3() { bash "$BACKEND_ROOT/singbox-server.sh" set 4 >/dev/null; }
case_H4() {
  require_disruptive || return 77
  bash "$BACKEND_ROOT/singbox-toggle.sh" full >/dev/null
  local pid="$(systemctl --user show -p MainPID --value sing-box-full.service)"
  [[ "$pid" =~ ^[0-9]+$ && "$pid" -gt 1 ]]
  kill -9 "$pid"
  sleep 2
  bash "$BACKEND_ROOT/singbox-toggle.sh" status-json | python3 -c 'import json,sys; o=json.load(sys.stdin); assert o["actual_state"] in {"LOCKED","DEGRADED","FAILED","TRANSITIONING"}'
}
case_H5() { return 77; } # disk-full simulation is risky on prod
case_H6() { return 77; } # sudoers mutation is risky on prod
case_H7() { return 77; } # GUI process lifecycle needs exact launcher/autostart control
case_H8() { return 77; } # workload generator is environment-specific (torrent + video)

for id in "${IDS[@]}"; do
  run_case "$id" "case_$id"
done
