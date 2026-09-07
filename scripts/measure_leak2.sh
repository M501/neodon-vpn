#!/bin/bash
# Clean A/B: forced-via-wlan0 to a REACHABLE host.
# full: must FAIL fast (rc=7 REJECT). smart/off: must print exit IP.
LOG=/tmp/leak2-measure.log
: > "$LOG"
stamp() { date +%T.%N | cut -c1-12; }
forced() { curl -s -4 -m 4 --interface wlan0 https://api.ipify.org 2>/dev/null || echo "rc=$?"; }
echo "=== $(stamp) normalize smart..." >> "$LOG"
bash ~/AI/singbox/singbox-toggle.sh smart >> "$LOG" 2>&1
sleep 3
echo "--- $(stamp) smart forced: $(forced)" >> "$LOG"
T0=$(date +%s)
bash ~/AI/singbox/singbox-toggle.sh full >> "$LOG" 2>&1
echo "--- $(stamp) FULL-TOOK-$(( $(date +%s) - T0 ))s forced: $(forced)" >> "$LOG"
bash ~/AI/singbox/singbox-toggle.sh off >> "$LOG" 2>&1
sleep 3
echo "--- $(stamp) off forced: $(forced)" >> "$LOG"
echo "--- $(stamp) off iprules:" >> "$LOG"
ip rule show >> "$LOG" 2>&1
echo "--- $(stamp) off normal: $(curl -s -m 5 https://api.ipify.org 2>/dev/null || echo rc=$?)" >> "$LOG"
T0=$(date +%s)
bash ~/AI/singbox/singbox-toggle.sh smart >> "$LOG" 2>&1
echo "--- $(stamp) back-smart-TOOK-$(( $(date +%s) - T0 ))s" >> "$LOG"
echo DONE >> "$LOG"
