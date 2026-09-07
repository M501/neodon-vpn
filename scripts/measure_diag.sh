#!/bin/bash
# Diag: is REJECT really installed? does forced egress really bypass?
LOG=/tmp/diag-measure.log
: > "$LOG"
stamp() { date +%T.%N | cut -c1-12; }
echo "=== $(stamp) mode=$(cat ~/AI/singbox/.mode)" >> "$LOG"
echo "--- rules with prio 20:" >> "$LOG"
sudo -n firewall-cmd --direct --get-all-rules 2>/dev/null | grep 'OUTPUT_direct 20 ' >> "$LOG" 2>&1
echo "--- total rules: $(sudo -n firewall-cmd --direct --get-all-rules 2>/dev/null | wc -l)" >> "$LOG"
echo "--- forced curl verbose-code:" >> "$LOG"
curl -s -4 -m 4 --interface wlan0 -o /dev/null -w "code=%{http_code} time=%{time_total}\n" https://1.1.1.1 >> "$LOG" 2>&1
echo "--- nft OUTPUT_direct:" >> "$LOG"
sudo -n nft list chain inet firewalld filter_OUTPUT 2>&1 | head -n 8 >> "$LOG"
echo DONE >> "$LOG"
