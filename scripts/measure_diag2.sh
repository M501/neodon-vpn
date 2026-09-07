#!/bin/bash
# Why did full toggle take 21s? normal-path egress + ip rules + phases.
LOG=/tmp/diag2-measure.log
: > "$LOG"
stamp() { date +%T.%N | cut -c1-12; }
echo "=== $(stamp) mode=$(cat ~/AI/singbox/.mode)" >> "$LOG"
s=$(date +%s%N); N=$(curl -s -m 5 -o /dev/null -w "%{http_code}" http://8.8.8.8/ 2>/dev/null); echo "--- normal-curl: $N $(( ($(date +%s%N) - s) / 1000000 ))ms" >> "$LOG"
echo "--- ip rules:" >> "$LOG"
ip rule show >> "$LOG" 2>&1
echo "--- full phases:" >> "$LOG"
bash /tmp/measure_fullphases.sh >/dev/null 2>&1
grep 'ks-install\|exit-curl\|wait-active\|tun-poll\|svc-start' /tmp/fullphase-measure.log >> "$LOG"
echo DONE >> "$LOG"
