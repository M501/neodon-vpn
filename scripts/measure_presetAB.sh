#!/bin/bash
# A/B proof: the Traffic tab drives reality. Same youtube, two presets.
LOG=/tmp/presetab-measure.log
: > "$LOG"
stamp() { date +%T.%N | cut -c1-12; }
exitip() { curl -s -4 -m 6 https://api.ipify.org 2>/dev/null || echo FAIL; }
echo "=== $(stamp) start profile=$(cat ~/AI/singbox/.profile) exit=$(exitip)" >> "$LOG"
echo "--- $(stamp) youtube oracle: $(python3 /tmp/probe_routing.py ~/AI/singbox/config.json youtube.com)" >> "$LOG"
~/AI/neodon-hostctl profile popular-ai >> "$LOG" 2>&1
sleep 6
echo "=== $(stamp) now profile=$(cat ~/AI/singbox/.profile) exit=$(exitip)" >> "$LOG"
echo "--- $(stamp) youtube oracle: $(python3 /tmp/probe_routing.py ~/AI/singbox/config.json youtube.com)" >> "$LOG"
~/AI/neodon-hostctl profile ru-bez-vpn >> "$LOG" 2>&1
sleep 6
echo "=== $(stamp) back profile=$(cat ~/AI/singbox/.profile) exit=$(exitip)" >> "$LOG"
echo "--- $(stamp) youtube oracle: $(python3 /tmp/probe_routing.py ~/AI/singbox/config.json youtube.com)" >> "$LOG"
echo DONE >> "$LOG"
