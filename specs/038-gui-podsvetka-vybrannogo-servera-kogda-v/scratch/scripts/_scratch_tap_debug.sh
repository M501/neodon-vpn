#!/bin/bash
# Run the instrumented build, do one vertical swipe, dump what the card actually saw.
set -u
export XDG_RUNTIME_DIR=/run/user/1000
export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus
export WAYLAND_DISPLAY=wayland-0
export DISPLAY=:0
DBG=/home/m26/AI/neodon-vpn/neodon-vpn-dbg.py
SS=/home/m26/AI/singbox/singbox-server.sh

for p in /proc/[0-9]*; do
  pid=${p#/proc/}
  if tr '\0' ' ' < "$p/cmdline" 2>/dev/null | grep -q "AI/neodon-vpn/neodon-vpn"; then
    kill "$pid" 2>/dev/null
  fi
done
sleep 3
rm -f /home/m26/tap_debug.log
systemd-run --user --unit=neodon-gui-dbg --collect \
  --setenv=XDG_RUNTIME_DIR=/run/user/1000 \
  --setenv=DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus \
  --setenv=WAYLAND_DISPLAY=wayland-0 --setenv=DISPLAY=:0 \
  --setenv=QT_QPA_PLATFORMTHEME=kde \
  /usr/bin/python3 "$DBG" >/dev/null 2>&1
sleep 6
pgrep -af "neodon-vpn-dbg.py" | head -2

bash "$SS" set 0 | tail -1
sleep 8
echo "--- selection before swipe ---"
python3 /tmp/selidx.py

echo "--- vertical swipe over the card (press 1212,770 -> release 1212,482) ---"
python3 /tmp/touch_drag.py 1212 770 1212 482 16 14
sleep 3
echo "--- what the card saw ---"
cat /home/m26/tap_debug.log 2>&1 | tail -12
echo "--- selection after swipe ---"
python3 /tmp/selidx.py

echo "--- cleanup: back to the live build ---"
for p in /proc/[0-9]*; do
  pid=${p#/proc/}
  if tr '\0' ' ' < "$p/cmdline" 2>/dev/null | grep -q "neodon-vpn-dbg.py"; then
    kill "$pid" 2>/dev/null
  fi
done
sleep 3
systemd-run --user --unit=neodon-gui-live --collect \
  --setenv=XDG_RUNTIME_DIR=/run/user/1000 \
  --setenv=DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus \
  --setenv=WAYLAND_DISPLAY=wayland-0 --setenv=DISPLAY=:0 \
  --setenv=QT_QPA_PLATFORMTHEME=kde \
  /usr/bin/python3 /home/m26/AI/neodon-vpn/neodon-vpn.py >/dev/null 2>&1
sleep 5
pgrep -af "AI/neodon-vpn/neodon-vpn.py" | head -2
bash "$SS" set 0 | tail -1
