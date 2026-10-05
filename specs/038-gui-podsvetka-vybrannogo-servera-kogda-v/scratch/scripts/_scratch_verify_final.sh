#!/bin/bash
# Stage 5: final touch-behaviour proof (swipes vertical-only) + live-node marker.
set -u
export XDG_RUNTIME_DIR=/run/user/1000
export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus
export WAYLAND_DISPLAY=wayland-0
export DISPLAY=:0
HOOK=/home/m26/AI/neodon-vpn/gui-action.json
SS=/home/m26/AI/singbox/singbox-server.sh
TG=/home/m26/AI/singbox/singbox-toggle.sh
OX=468; OY=52

grab() {
  rm -f "$1"
  printf '%s' "{\"action\":\"grab\",\"path\":\"$1\"}" > "$HOOK"
  sleep 3
  [ -s "$1" ] && echo "grab ok: $1" || echo "GRAB FAILED: $1"
}
frame() { python3 /tmp/frame.py "$1" | sed -n '2p'; }

echo "########## restore selection 0 ##########"
bash "$SS" set 0 | tail -1
sleep 9
python3 /tmp/selidx.py
grab /home/m26/f_base.png
frame /home/m26/f_base.png

echo "########## swipe right, press+release INSIDE the window ##########"
python3 /tmp/touch_drag.py $((OX + 744)) $((OY + 718)) $((OX + 952)) $((OY + 718)) 16 14
sleep 2
grab /home/m26/f_r1.png
python3 /tmp/shift2.py /home/m26/f_base.png /home/m26/f_r1.png | tail -1
python3 /tmp/selidx.py

echo "########## swipe left, back, inside the window ##########"
python3 /tmp/touch_drag.py $((OX + 952)) $((OY + 718)) $((OX + 744)) $((OY + 718)) 16 14
sleep 2
grab /home/m26/f_l1.png
python3 /tmp/shift2.py /home/m26/f_r1.png /home/m26/f_l1.png | tail -1
python3 /tmp/selidx.py

echo "########## swipe starting OUTSIDE the window (stray-release probe) ##########"
python3 /tmp/touch_drag.py 1562 $((OY + 718)) $((OX + 744)) $((OY + 718)) 16 14
sleep 3
python3 /tmp/selidx.py

echo "########## vertical swipe (control) ##########"
python3 /tmp/touch_drag.py $((OX + 744)) $((OY + 718)) $((OX + 744)) $((OY + 430)) 16 14
sleep 2
grab /home/m26/f_v1.png
python3 /tmp/shift2.py /home/m26/f_l1.png /home/m26/f_v1.png | tail -1
python3 /tmp/selidx.py

echo "########## restore selection 0 ##########"
bash "$SS" set 0 | tail -1
sleep 9
python3 /tmp/selidx.py

echo "########## live-node marker: VPN on (smart) ##########"
bash "$TG" smart | tail -2
sleep 10
curl -s -m 2 http://127.0.0.1:9090/proxies/proxy; echo
grab /home/m26/f_on.png
frame /home/m26/f_on.png
python3 /tmp/selidx.py

echo "########## back OFF (owner's state) ##########"
bash "$TG" off | tail -2
sleep 6
cat /home/m26/AI/singbox/.mode
systemctl --user is-active sing-box.service sing-box-full.service sing-box-proxy.service 2>&1 | tr '\n' ' '
echo
curl -s -m 2 -o /dev/null -w 'api after off: %{http_code}\n' http://127.0.0.1:9090/proxies/proxy
python3 /tmp/selidx.py
grab /home/m26/f_final.png
frame /home/m26/f_final.png
