#!/bin/bash
# Post-mortem: what state is the device in after the interrupted live QA run?
set -u
export XDG_RUNTIME_DIR=/run/user/1000
export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus
SB=/home/m26/AI/singbox
QA=/home/m26/AI/neodon-qa

echo "=== mode / units / internet ==="
echo "mode: $(cat "$SB/.mode" 2>/dev/null)"
echo "desired: $(cat "$HOME/.desired" 2>/dev/null || echo none)"
echo "units: $(systemctl --user is-active sing-box.service sing-box-full.service sing-box-proxy.service 2>&1 | tr '\n' ' ')"
echo "tun0: $(ip link show tun0 2>/dev/null | head -1 || echo none)"
echo "prio-20 REJECT rules: $(sudo -n firewall-cmd --direct --get-all-rules 2>/dev/null | grep -c 'filter OUTPUT_direct 20 ' || true)"
echo "resolv: $(head -1 /etc/resolv.conf)"
echo "exit-ip: $(curl -s -m 8 https://api.ipify.org 2>/dev/null || echo FAIL)"
echo "GUI: $(pgrep -af 'AI/neodon-vpn/neodon-vpn.py' | head -1)"

echo
echo "=== is the QA run still going? ==="
pgrep -af "run-all.sh|l3_|l4_" | head -5 || echo "(no QA processes)"
ls -la "$QA/qa-results/" 2>/dev/null

echo
echo "=== partial QA raw log (tail) ==="
tail -60 "$QA/qa-results/raw.log" 2>/dev/null

echo
echo "=== per-section results if the report exists ==="
cat "$QA/qa-results/report.md" 2>/dev/null | head -60
