#!/bin/bash
# Split the post-full null window: route vs DNS vs HTTP readiness.
LOG=/tmp/fulltrans-measure.log
: > "$LOG"
stamp() { date +%T.%N | cut -c1-12; }
echo "=== $(stamp) toggle full..." >> "$LOG"
bash ~/AI/singbox/singbox-toggle.sh full >> "$LOG" 2>&1
echo "=== $(stamp) full done, toggle smart..." >> "$LOG"
T0=$(date +%s%N)
bash ~/AI/singbox/singbox-toggle.sh smart >> "$LOG" 2>&1
echo "=== $(stamp) smart-toggle returned in $(( ($(date +%s%N) - T0) / 1000000 ))ms" >> "$LOG"
for i in $(seq 1 14); do
  S=$(bash ~/AI/singbox/singbox-toggle.sh status-json 2>/dev/null | cut -c60-130)
  R=$(ip route get 1.1.1.1 2>/dev/null | head -n 1 | cut -c1-80)
  s=$(date +%s%N); getent ahostsv4 api.ipify.org >/dev/null 2>&1; D=$(( ($(date +%s%N) - s) / 1000000 ))
  s=$(date +%s%N); C=$(curl -s -m 2 -o /dev/null -w "%{http_code}" https://api.ipify.org 2>/dev/null); H=$(( ($(date +%s%N) - s) / 1000000 ))
  echo "--- $(stamp) [$i] $S | route: $R | dns:${D}ms curl:${C}/${H}ms" >> "$LOG"
done
echo DONE >> "$LOG"
