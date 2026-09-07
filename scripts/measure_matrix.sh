#!/bin/bash
# Fail-closed A/B proof + full switch matrix with timings.
# LOCKED proof: curl forced via physical iface must FAIL in full (REJECT),
# and SUCCEED in smart/off (no REJECT). Honest exit check via default route.
LOG=/tmp/matrix-measure.log
: > "$LOG"
stamp() { date +%T.%N | cut -c1-12; }
PHY=$(ip route show default 2>/dev/null | awk '/default/ {print $5; exit}')
echo "=== phys-iface: $PHY" >> "$LOG"
forced() { curl -s -4 -m 3 --interface "$PHY" -o /dev/null -w "%{http_code}" https://1.1.1.1 2>/dev/null || echo FAIL; }
state() { bash ~/AI/singbox/singbox-toggle.sh status-json 2>/dev/null | cut -c60-200; }
for M in full smart off smart; do
  T0=$(date +%s)
  bash ~/AI/singbox/singbox-toggle.sh "$M" >> "$LOG" 2>&1
  DT=$(( $(date +%s) - T0 ))
  F=$(forced)
  echo "=== $(stamp) mode=$M toggle=${DT}s forced-egress=$F $(state)" >> "$LOG"
  sleep 2
done
echo DONE >> "$LOG"
