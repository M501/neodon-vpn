#!/bin/bash
# Repro probe: does a horizontal finger swipe pan the Neodon GUI content?
# (before/after window grabs via the app's own gui-action hook)
set -u
export XDG_RUNTIME_DIR=/run/user/1000
export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus
export WAYLAND_DISPLAY=wayland-0
export DISPLAY=:0
HOOK=/home/m26/AI/neodon-vpn/gui-action.json

grab() {  # $1 = output png
  rm -f "$1"
  printf '%s' "{\"action\":\"grab\",\"path\":\"$1\"}" > "$HOOK"
  sleep 3
  if [ -s "$1" ]; then echo "grab ok: $1 ($(stat -c%s "$1") bytes)"; else echo "grab FAILED: $1"; fi
}

qdbus6 org.kde.screensaver /ScreenSaver org.freedesktop.ScreenSaver.SimulateUserActivity >/dev/null 2>&1
sleep 1

echo "=== A: horizontal swipe (right) across the servers area ==="
grab /home/m26/g_before.png
python3 /tmp/touch_drag.py 900 700 1250 700 16 14
sleep 1
grab /home/m26/g_after_h.png
echo "--- shift before->after_h ---"
python3 /tmp/shift.py /home/m26/g_before.png /home/m26/g_after_h.png

echo "=== B: horizontal swipe back (left) ==="
python3 /tmp/touch_drag.py 1250 700 900 700 16 14
sleep 1
grab /home/m26/g_after_h2.png
echo "--- shift after_h->after_h2 ---"
python3 /tmp/shift.py /home/m26/g_after_h.png /home/m26/g_after_h2.png

echo "=== C: control, vertical swipe ==="
python3 /tmp/touch_drag.py 900 700 900 420 16 14
sleep 1
grab /home/m26/g_after_v.png
echo "--- shift after_h2->after_v ---"
python3 /tmp/shift.py /home/m26/g_after_h2.png /home/m26/g_after_v.png
