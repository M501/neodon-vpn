#!/bin/bash
# Stage 4: tap selects + highlights instantly; swipes are vertical-only.
set -u
export XDG_RUNTIME_DIR=/run/user/1000
export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus
export WAYLAND_DISPLAY=wayland-0
export DISPLAY=:0
HOOK=/home/m26/AI/neodon-vpn/gui-action.json
SS=/home/m26/AI/singbox/singbox-server.sh
OX=468; OY=52     # client origin on the panel (locate_grab.py)

grab() {
  rm -f "$1"
  printf '%s' "{\"action\":\"grab\",\"path\":\"$1\"}" > "$HOOK"
  sleep 3
  [ -s "$1" ] && echo "grab ok: $1" || echo "GRAB FAILED: $1"
}

# right column, second grid row (client 744,718) on the panel:
TX=$((OX + 744)); TY=$((OY + 718))

echo "########## STEP E: TAP the card at client(744,718) = grid index 3 ##########"
python3 /tmp/selidx.py
python3 /tmp/touch_tap.py "$TX" "$TY" 90
sleep 4
python3 /tmp/selidx.py
grab /home/m26/t_tap.png
python3 /tmp/frame.py /home/m26/t_tap.png | tail -2

echo "########## STEP F: restore index 0 ##########"
bash "$SS" set 0 | tail -1
sleep 9
python3 /tmp/selidx.py
grab /home/m26/s_base.png
python3 /tmp/frame.py /home/m26/s_base.png | tail -2

echo "########## STEP G: horizontal swipe right (must NOT move content) ##########"
python3 /tmp/touch_drag.py "$TX" "$TY" $((TX + 350)) "$TY" 16 14
sleep 2
python3 /tmp/selidx.py
grab /home/m26/s_right.png
python3 /tmp/shift2.py /home/m26/s_base.png /home/m26/s_right.png | tail -1

echo "########## STEP H: horizontal swipe left (must NOT move content) ##########"
python3 /tmp/touch_drag.py $((TX + 350)) "$TY" "$TX" "$TY" 16 14
sleep 2
grab /home/m26/s_left.png
python3 /tmp/shift2.py /home/m26/s_right.png /home/m26/s_left.png | tail -1

echo "########## STEP I: vertical swipe (control: MUST scroll) ##########"
python3 /tmp/touch_drag.py "$TX" "$TY" "$TX" $((TY - 260)) 16 14
sleep 2
grab /home/m26/s_vert.png
python3 /tmp/shift2.py /home/m26/s_left.png /home/m26/s_vert.png | tail -1

echo "########## final state ##########"
python3 /tmp/selidx.py
cat /home/m26/AI/singbox/.mode
systemctl --user is-active sing-box.service sing-box-full.service sing-box-proxy.service 2>&1 | tr '\n' ' '
echo
