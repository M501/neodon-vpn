#!/bin/bash
# Reproduce G3 (leftover fail-closed rules after 'off') with tracing, then check I2/I3
# prerequisites, then leave the owner's state (off).
set -u
export XDG_RUNTIME_DIR=/run/user/1000
export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus
SB=/home/m26/AI/singbox
QA=/home/m26/AI/neodon-qa

echo "=== G3 reproduction: full -> off, then query the firewall ==="
bash "$SB/singbox-toggle.sh" full >/dev/null 2>&1; echo "full rc=$?"
sleep 3
rules_full="$(sudo -n firewall-cmd --direct --get-all-rules 2>&1)"; echo "query(full) rc=$?"
echo "prio-20 in full mode: $(grep -c 'OUTPUT_direct 20 ' <<<"$rules_full" || true)"

bash "$SB/singbox-toggle.sh" off >/dev/null 2>&1; echo "off rc=$?"
sleep 2
rules_off="$(sudo -n firewall-cmd --direct --get-all-rules 2>&1)"; echo "query(off) rc=$?"
echo "prio-20 after off: $(grep -c 'OUTPUT_direct 20 ' <<<"$rules_off" || true)"
echo "mode now: $(cat "$SB/.mode")"
echo "internet: $(curl -s -m 8 https://api.ipify.org 2>/dev/null || echo FAIL)"
echo "resolv: $(head -1 /etc/resolv.conf)"

echo
echo "=== I2/I3 prerequisites (release cases) ==="
sed -n '1,40p' "$QA/qa/release/l4_release.sh" 2>/dev/null | grep -n "case_I" -A 3
ls -la "$QA/release/" 2>/dev/null | head -5 || echo "release/ dir is NOT in the QA snapshot (that is why I2/I3 fail instantly)"

echo
echo "=== final state check ==="
systemctl --user is-active sing-box.service sing-box-full.service sing-box-proxy.service 2>&1 | tr '\n' ' '; echo
echo "GUI: $(pgrep -af 'AI/neodon-vpn/neodon-vpn.py' | head -1)"
