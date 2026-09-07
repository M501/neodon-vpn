#!/bin/bash
# One-shot measurement: where do the ~10s of proxy<->smart switching go?
LOG=/tmp/switch-measure.log
: > "$LOG"
stamp() { date +%T.%N | cut -c1-12; }
echo "=== $(stamp) start, mode=$(cat ~/AI/singbox/.mode 2>/dev/null)" >> "$LOG"
echo "=== $(stamp) toggle proxy..." >> "$LOG"
time bash ~/AI/singbox/singbox-toggle.sh proxy >> "$LOG" 2>&1
echo "=== $(stamp) toggle-proxy returned" >> "$LOG"
for i in $(seq 1 20); do
  echo "--- $(stamp) poll $i: $(bash ~/AI/singbox/singbox-toggle.sh status-json 2>/dev/null | tr -d '\n' | cut -c1-220)" >> "$LOG"
  sleep 1
done
echo "=== $(stamp) toggle smart back..." >> "$LOG"
time bash ~/AI/singbox/singbox-toggle.sh smart >> "$LOG" 2>&1
echo "=== $(stamp) toggle-smart returned" >> "$LOG"
for i in $(seq 1 12); do
  echo "--- $(stamp) pollS $i: $(bash ~/AI/singbox/singbox-toggle.sh status-json 2>/dev/null | tr -d '\n' | cut -c1-220)" >> "$LOG"
  sleep 1
done
echo DONE >> "$LOG"
