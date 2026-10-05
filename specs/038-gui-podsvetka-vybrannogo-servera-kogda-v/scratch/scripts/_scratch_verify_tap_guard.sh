#!/bin/bash
# Stage 6: A/B for the tap guard — real tap must select, swipe must not.
set -u
export XDG_RUNTIME_DIR=/run/user/1000
export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus
export WAYLAND_DISPLAY=wayland-0
export DISPLAY=:0
HOOK=/home/m26/AI/neodon-vpn/gui-action.json
SS=/home/m26/AI/singbox/singbox-server.sh
OX=468; OY=52

grab() { rm -f "$1"; printf '%s' "{\"action\":\"grab\",\"path\":\"$1\"}" > "$HOOK"; sleep 3; [ -s "$1" ] && echo "grab ok: $1" || echo "GRAB FAILED $1"; }

echo "########## A: real TAP on the right-column second-row card (index 3) ##########"
bash "$SS" set 0 | tail -1
sleep 9
python3 /tmp/selidx.py
python3 /tmp/touch_tap.py $((OX + 744)) $((OY + 718)) 90
sleep 4
echo "-> after tap:"; python3 /tmp/selidx.py
grab /home/m26/g_tap.png
python3 /tmp/frame.py /home/m26/g_tap.png | sed -n '2p'

echo "########## B: vertical swipe (press on a card, release elsewhere) must NOT select ##########"
bash "$SS" set 0 | tail -1
sleep 9
python3 /tmp/selidx.py
python3 /tmp/touch_drag.py $((OX + 744)) $((OY + 718)) $((OX + 744)) $((OY + 430)) 16 14
sleep 3
echo "-> after swipe:"; python3 /tmp/selidx.py
grab /home/m26/g_swipe.png
python3 /tmp/frame.py /home/m26/g_swipe.png | sed -n '2p'

echo "########## C: restore owner's selection (0) + state ##########"
bash "$SS" set 0 | tail -1
sleep 6
python3 /tmp/selidx.py
cat /home/m26/AI/singbox/.mode
systemctl --user is-active sing-box.service sing-box-full.service sing-box-proxy.service 2>&1 | tr '\n' ' '
echo
