#!/bin/bash
# Deploy the current repo GUI to the live device and restart it (backup kept).
set -u
export XDG_RUNTIME_DIR=/run/user/1000
export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus
export WAYLAND_DISPLAY=wayland-0
export DISPLAY=:0
GUIF=/home/m26/AI/neodon-vpn/neodon-vpn.py
echo "live md5 (before): $(md5sum "$GUIF" | cut -d' ' -f1)"
for p in /proc/[0-9]*; do
  pid=${p#/proc/}
  if tr '\0' ' ' < "$p/cmdline" 2>/dev/null | grep -q "AI/neodon-vpn/neodon-vpn.py"; then
    echo "killing $pid"; kill "$pid" 2>/dev/null
  fi
done
sleep 3
systemd-run --user --unit=neodon-gui-live --collect \
  --setenv=XDG_RUNTIME_DIR=/run/user/1000 \
  --setenv=DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus \
  --setenv=WAYLAND_DISPLAY=wayland-0 --setenv=DISPLAY=:0 \
  --setenv=QT_QPA_PLATFORMTHEME=kde \
  /usr/bin/python3 "$GUIF" >/dev/null 2>&1
sleep 6
echo "live md5 (after): $(md5sum "$GUIF" | cut -d' ' -f1)"
systemctl --user is-active neodon-gui-live.service
pgrep -af neodon-vpn.py | grep -v grep
