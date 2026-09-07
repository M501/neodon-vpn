#!/bin/bash
# Correct leak matrix: port 80 to a NON-allowlisted IP.
# full: REJECT -> curl exit 7. smart/off: direct -> HTTP 301/404 (exit 0).
LOG=/tmp/leak-measure.log
: > "$LOG"
stamp() { date +%T.%N | cut -c1-12; }
PHY=$(ip route show default 2>/dev/null | awk '/default/ {print $5; exit}')
probe() { curl -s -4 -m 3 --interface "$PHY" -o /dev/null -w "%{http_code}" http://8.8.8.8/ 2>/dev/null; echo ":rc=$?"; }
for M in full smart off smart; do
  T0=$(date +%s)
  bash ~/AI/singbox/singbox-toggle.sh "$M" >> "$LOG" 2>&1
  DT=$(( $(date +%s) - T0 ))
  echo "=== $(stamp) mode=$M toggle=${DT}s leak-probe=$(probe) $(bash ~/AI/singbox/singbox-toggle.sh status-json 2>/dev/null | cut -c60-160)" >> "$LOG"
  sleep 2
done
echo DONE >> "$LOG"
