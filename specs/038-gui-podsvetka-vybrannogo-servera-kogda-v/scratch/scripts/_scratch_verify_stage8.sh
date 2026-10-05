#!/bin/bash
# Stage 8: tap test from a known scroll position (page back to top via the app hook).
set -u
export XDG_RUNTIME_DIR=/run/user/1000
export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus
export WAYLAND_DISPLAY=wayland-0
export DISPLAY=:0
HOOK=/home/m26/AI/neodon-vpn/gui-action.json
SS=/home/m26/AI/singbox/singbox-server.sh
OX=468; OY=52

grab() { rm -f "$1"; printf '%s' "{\"action\":\"grab\",\"path\":\"$1\"}" > "$HOOK"; sleep 3; [ -s "$1" ] && echo "grab ok: $1" || echo "GRAB FAILED $1"; }
frame() { python3 /tmp/frame.py "$1" | sed -n '2p'; }

echo "########## scroll the page back to the top (app hook) ##########"
printf '%s' '{"action":"scroll","by":-3000}' > "$HOOK"
sleep 3
python3 /tmp/selidx.py
grab /home/m26/p_top.png
frame /home/m26/p_top.png

echo "########## real TAP on the index-3 card (client 744,718) ##########"
python3 /tmp/touch_tap.py $((OX + 744)) $((OY + 718)) 90
sleep 4
echo "-> after tap:"; python3 /tmp/selidx.py
grab /home/m26/p_tap.png
frame /home/m26/p_tap.png

echo "########## scroll down/up by hook: must NOT select ##########"
printf '%s' '{"action":"scroll","by":300}' > "$HOOK"
sleep 3
printf '%s' '{"action":"scroll","by":-300}' > "$HOOK"
sleep 3
python3 /tmp/selidx.py

echo "########## restore owner's state ##########"
bash "$SS" set 0 | tail -1
sleep 7
python3 /tmp/selidx.py
cat /home/m26/AI/singbox/.mode
systemctl --user is-active sing-box.service sing-box-full.service sing-box-proxy.service 2>&1 | tr '\n' ' '
echo
grab /home/m26/p_final.png
frame /home/m26/p_final.png
