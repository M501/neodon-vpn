#!/bin/bash
# Stage 7: after the scroll-guard — tap selects, scroll does not, vertical scroll works.
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

echo "########## 1) vertical swipe over a card: must scroll, must NOT select ##########"
bash "$SS" set 0 | tail -1
sleep 9
python3 /tmp/selidx.py
grab /home/m26/k_top.png
frame /home/m26/k_top.png
python3 /tmp/touch_drag.py $((OX + 744)) $((OY + 718)) $((OX + 744)) $((OY + 430)) 16 14
sleep 2
grab /home/m26/k_scrolled.png
frame /home/m26/k_scrolled.png
echo "-> selection after swipe:"; python3 /tmp/selidx.py

echo "########## 2) horizontal swipes: must not move content, must not select ##########"
python3 /tmp/touch_drag.py $((OX + 744)) $((OY + 600)) $((OX + 952)) $((OY + 600)) 16 14
sleep 2
grab /home/m26/k_r.png
python3 /tmp/shift2.py /home/m26/k_scrolled.png /home/m26/k_r.png | tail -1
python3 /tmp/touch_drag.py $((OX + 952)) $((OY + 600)) $((OX + 744)) $((OY + 600)) 16 14
sleep 2
grab /home/m26/k_l.png
python3 /tmp/shift2.py /home/m26/k_r.png /home/m26/k_l.png | tail -1
echo "-> selection:"; python3 /tmp/selidx.py

echo "########## 3) real TAP on index-3 card: must select it ##########"
bash "$SS" set 0 | tail -1
sleep 9
python3 /tmp/touch_tap.py $((OX + 744)) $((OY + 718)) 90
sleep 4
python3 /tmp/selidx.py
grab /home/m26/k_tap.png
frame /home/m26/k_tap.png

echo "########## 4) restore owner's state ##########"
bash "$SS" set 0 | tail -1
sleep 6
python3 /tmp/selidx.py
cat /home/m26/AI/singbox/.mode
systemctl --user is-active sing-box.service sing-box-full.service sing-box-proxy.service 2>&1 | tr '\n' ' '
echo
grab /home/m26/k_final.png
frame /home/m26/k_final.png
