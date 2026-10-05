#!/bin/bash
# Verify the honest "off": no leftover fail-closed REJECT, internet really back.
set -u
export XDG_RUNTIME_DIR=/run/user/1000
export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus
TG=/home/m26/AI/singbox/singbox-toggle.sh

echo "=== copy in place ==="
ls -la "$TG"
md5sum "$TG"

echo "=== ON (smart) ==="
bash "$TG" smart 2>&1 | tail -2
sleep 10
cat /home/m26/AI/singbox/.mode

echo "=== OFF (the message must be honest) ==="
bash "$TG" off 2>&1 | tail -3
sleep 5
echo "mode now: $(cat /home/m26/AI/singbox/.mode)"

echo "=== leftover fail-closed rules? ==="
sudo -n firewall-cmd --direct --get-all-rules 2>/dev/null | grep -c 'filter OUTPUT_direct 20 ' || echo 0

echo "=== internet via ISP ==="
curl -s -m 8 https://api.ipify.org || echo "(no exit ip)"
echo
echo "=== units ==="
systemctl --user is-active sing-box.service sing-box-full.service sing-box-proxy.service 2>&1 | tr '\n' ' '
echo
