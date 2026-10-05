#!/bin/bash
# Stage 2: restart the live GUI on the NEW build, then grab + locate + card analysis.
set -u
export XDG_RUNTIME_DIR=/run/user/1000
export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus
export WAYLAND_DISPLAY=wayland-0
export DISPLAY=:0
export QT_QPA_PLATFORMTHEME=kde
GUIF=/home/m26/AI/neodon-vpn/neodon-vpn.py
HOOK=/home/m26/AI/neodon-vpn/gui-action.json

echo "=== current GUI units/processes ==="
systemctl --user list-units --all --no-legend 2>/dev/null | grep -i neodon || echo "(no neodon units)"
for p in /proc/[0-9]*; do
  pid=${p#/proc/}
  if tr '\0' ' ' < "$p/cmdline" 2>/dev/null | grep -q "AI/neodon-vpn/neodon-vpn.py"; then
    echo "live GUI pid=$pid started=$(ps -o lstart= -p "$pid" 2>/dev/null)"
  fi
done

echo "=== stopping old instances ==="
systemctl --user stop neodon-gui-live.service 2>/dev/null
for p in /proc/[0-9]*; do
  pid=${p#/proc/}
  if tr '\0' ' ' < "$p/cmdline" 2>/dev/null | grep -q "AI/neodon-vpn/neodon-vpn.py"; then
    kill "$pid" 2>/dev/null && echo "killed $pid"
  fi
done
sleep 3

echo "=== starting new build ==="
systemd-run --user --unit=neodon-gui-live --collect \
  --setenv=XDG_RUNTIME_DIR=/run/user/1000 \
  --setenv=DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus \
  --setenv=WAYLAND_DISPLAY=wayland-0 --setenv=DISPLAY=:0 \
  --setenv=QT_QPA_PLATFORMTHEME=kde \
  /usr/bin/python3 "$GUIF" >/dev/null 2>&1
sleep 6
systemctl --user is-active neodon-gui-live.service
for p in /proc/[0-9]*; do
  pid=${p#/proc/}
  if tr '\0' ' ' < "$p/cmdline" 2>/dev/null | grep -q "AI/neodon-vpn/neodon-vpn.py"; then
    echo "new GUI pid=$pid"
    stat -c '%y %n' "$GUIF"
  fi
done

echo "=== grab window ==="
rm -f /home/m26/g_new.png
printf '%s' '{"action":"grab","path":"/home/m26/g_new.png"}' > "$HOOK"
sleep 4
ls -la /home/m26/g_new.png 2>&1 || echo "GRAB FAILED"

echo "=== full-screen shot ==="
qdbus6 org.kde.screensaver /ScreenSaver org.freedesktop.ScreenSaver.SimulateUserActivity >/dev/null 2>&1
sleep 1
rm -f /home/m26/desk2.png
spectacle -f -b -n -o /home/m26/desk2.png >/dev/null 2>&1
ls -la /home/m26/desk2.png 2>&1

echo "=== locate grab inside screen ==="
python3 /tmp/locate_grab.py /home/m26/desk2.png /home/m26/g_new.png 2>&1 | tail -3

echo "=== card analysis ==="
python3 /tmp/cells.py /home/m26/g_new.png 2>&1 | tail -25

echo "=== selected-server.json ==="
cat /home/m26/AI/singbox/selected-server.json
