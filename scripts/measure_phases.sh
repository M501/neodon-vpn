#!/bin/bash
# Per-phase timing of the proxy branch (same steps as singbox-toggle.sh proxy).
LOG=/tmp/phase-measure.log
: > "$LOG"
stamp() { date +%T.%N | cut -c1-12; }
T() { local name=$1; shift; local s; s=$(date +%s%N); "$@" >>"$LOG" 2>&1; echo "=== $(stamp) [$name] $(( ($(date +%s%N) - s) / 1000000 ))ms" >> "$LOG"; }
echo "=== $(stamp) begin from mode=$(cat ~/AI/singbox/.mode 2>/dev/null)" >> "$LOG"
T stop1 systemctl --user stop sing-box.service
T stop2 systemctl --user stop sing-box-full.service
T stop3 systemctl --user stop sing-box-proxy.service
T fwflush bash ~/AI/singbox/killswitch.sh remove
T dnsfix bash ~/AI/singbox/dns-fix.sh apply
T ffproxy bash ~/AI/neodon-flatpak/firefox-proxy.sh apply
T start systemctl --user start sing-box-proxy.service
echo "=== $(stamp) all phases done, curl:" >> "$LOG"
curl -s -m 3 -x socks5h://127.0.0.1:10808 https://api.ipify.org >>"$LOG" 2>&1; echo >>"$LOG"
echo "=== $(stamp) end" >> "$LOG"
echo DONE
