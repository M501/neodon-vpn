#!/bin/bash
# Release the work sleep guard and put the owner's selection back (index 0 = AT).
set -u
export XDG_RUNTIME_DIR=/run/user/1000
export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus
SS=/home/m26/AI/singbox/singbox-server.sh

systemctl --user stop hermes-sleep-hold.service 2>/dev/null
systemctl --user reset-failed hermes-sleep-hold.service 2>/dev/null
sleep 1
echo "guard: $(systemctl --user is-active hermes-sleep-hold.service 2>&1)"
echo "hermes inhibitors: $(systemd-inhibit --list 2>/dev/null | grep -c 'hermes spec work')"

echo "=== restore owner's selection (index 0) ==="
bash "$SS" set 0 2>&1 | tail -1
sleep 6
cat /home/m26/AI/singbox/selected-server.json
echo
cat /home/m26/AI/singbox/.mode
systemctl --user is-active sing-box.service sing-box-full.service sing-box-proxy.service 2>&1 | tr '\n' ' '
echo
echo "gui: $(pgrep -af 'AI/neodon-vpn/neodon-vpn.py' | head -1)"
md5sum /home/m26/AI/neodon-vpn/neodon-vpn.py /home/m26/AI/neodon-vpn/flags/DE.png
