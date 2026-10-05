#!/bin/bash
set -u
export XDG_RUNTIME_DIR=/run/user/1000
export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus
export WAYLAND_DISPLAY=wayland-0
export DISPLAY=:0
HOOK=/home/m26/AI/neodon-vpn/gui-action.json
grab() { rm -f "$1"; printf '%s' "{\"action\":\"grab\",\"path\":\"$1\"}" > "$HOOK"; sleep 3; [ -s "$1" ] && echo "grab ok: $1" || echo "GRAB FAILED $1"; }
# finger moves DOWN -> content should scroll back up (proves vertical scrolling alive)
python3 /tmp/touch_drag.py 1212 482 1212 770 16 14
sleep 2
grab /home/m26/f_v2.png
python3 /tmp/shift2.py /home/m26/f_v1.png /home/m26/f_v2.png | tail -1
python3 /tmp/selidx.py
