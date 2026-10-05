#!/bin/bash
# Rescue: re-arm the sleep guard, diagnose the tunnel left ON by an interrupted test,
# then leave the owner's canonical state (VPN off, internet via ISP).
set -u
export XDG_RUNTIME_DIR=/run/user/1000
export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus
SB=/home/m26/AI/singbox

echo "=== arm sleep guard (PowerDevil suspends via sleep; keeper only blocks idle) ==="
systemd-run --user --unit=hermes-sleep-hold --collect \
  /usr/bin/systemd-inhibit --what=sleep:idle --mode=block --why="hermes spec work" \
  /usr/bin/sleep 7200 >/dev/null 2>&1
sleep 1
echo "guard: $(systemctl --user is-active hermes-sleep-hold.service)"

echo
echo "=== what is the tunnel doing right now? ==="
echo "mode: $(cat "$SB/.mode") / desired: $(cat "$HOME/.desired" 2>/dev/null || echo none)"
echo "units: $(systemctl --user is-active sing-box.service sing-box-full.service sing-box-proxy.service 2>&1 | tr '\n' ' ')"
echo "tun0: $(ip link show tun0 2>/dev/null | head -1 || echo none)"
echo "resolv: $(head -1 /etc/resolv.conf)"
echo "bare ipify: $(curl -s -m 6 https://api.ipify.org 2>/dev/null || echo FAIL)"
echo "socks ipify: $(curl -s -m 6 -x socks5h://127.0.0.1:10808 https://api.ipify.org 2>/dev/null || echo FAIL)"
echo "direct ya.ru: $(curl -s -m 6 -o /dev/null -w '%{http_code}' https://ya.ru 2>/dev/null || echo FAIL)"
echo "ping 1.1.1.1: $(ping -c1 -W2 1.1.1.1 >/dev/null 2>&1 && echo ok || echo FAIL)"
echo "wlan0: $(nmcli -t -f DEVICE,STATE device 2>/dev/null | grep wlan0)"

echo
echo "=== status-json (bounded) ==="
timeout 25 bash "$SB/singbox-toggle.sh" status-json 2>/dev/null | tail -1

echo
echo "=== canonical state: OFF ==="
bash "$SB/singbox-toggle.sh" off >/dev/null 2>&1; echo "off rc=$?"
sleep 5
echo "mode: $(cat "$SB/.mode")"
echo "units: $(systemctl --user is-active sing-box.service sing-box-full.service sing-box-proxy.service 2>&1 | tr '\n' ' ')"
echo "prio-20 rules: $(sudo -n firewall-cmd --direct --get-all-rules 2>/dev/null | grep -c 'OUTPUT_direct 20 ' || true)"
echo "resolv: $(head -1 /etc/resolv.conf)"
echo "internet: $(curl -s -m 8 https://api.ipify.org 2>/dev/null || echo FAIL)"
echo "GUI: $(pgrep -af 'AI/neodon-vpn/neodon-vpn.py' | head -1)"
echo "live md5: $(md5sum /home/m26/AI/neodon-vpn/neodon-vpn.py | cut -c1-8)"
