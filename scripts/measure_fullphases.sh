#!/bin/bash
# Phase breakdown of the FULL branch (mirrors singbox-toggle.sh full).
LOG=/tmp/fullphase-measure.log
: > "$LOG"
stamp() { date +%T.%N | cut -c1-12; }
T() { local name=$1; shift; local s; s=$(date +%s%N); "$@" >>"$LOG" 2>&1; echo "=== $(stamp) [$name] $(( ($(date +%s%N) - s) / 1000000 ))ms" >> "$LOG"; }
echo "=== $(stamp) begin" >> "$LOG"
T ff-restore bash ~/AI/neodon-flatpak/firefox-proxy.sh restore
T stop-all bash -c 'systemctl --user stop sing-box.service; systemctl --user stop sing-box-full.service; systemctl --user stop sing-box-proxy.service'
T fw-flush bash ~/AI/singbox/killswitch.sh remove
T dns-fix bash ~/AI/singbox/dns-fix.sh apply
T svc-start systemctl --user start sing-box-full.service
T wait-active bash -c 'for i in $(seq 1 25); do systemctl --user is-active sing-box-full.service >/dev/null 2>&1 && break; sleep 0.2; done'
T tun-poll bash -c 'for _t in $(seq 1 15); do ip link show tun0 >/dev/null 2>&1 && break; sleep 0.2; done'
T ks-install bash ~/AI/singbox/killswitch.sh install
T exit-curl curl -s -m 3 https://api.ipify.org
echo "=== $(stamp) end" >> "$LOG"
echo DONE
