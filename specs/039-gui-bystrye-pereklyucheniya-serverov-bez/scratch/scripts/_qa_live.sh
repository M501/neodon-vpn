#!/bin/bash
# Full LIVE QA matrix of the project suite (groups A-L), with restore-to-canon.
set -u
export XDG_RUNTIME_DIR=/run/user/1000
export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus
export WAYLAND_DISPLAY=wayland-0
export DISPLAY=:0
export QT_QPA_PLATFORMTHEME=kde
QA=/home/m26/AI/neodon-qa
export NEODON_REPO="$QA"
export NEODON_APP=/home/m26/AI/neodon-vpn/neodon-vpn.py
export NEODON_BACKEND=/home/m26/AI/singbox

# restart the GUI on the current build first (UI cases drive the live window)
for p in /proc/[0-9]*; do
  pid=${p#/proc/}
  if tr '\0' ' ' < "$p/cmdline" 2>/dev/null | grep -q "AI/neodon-vpn/neodon-vpn.py"; then kill "$pid" 2>/dev/null; fi
done
sleep 3
systemd-run --user --unit=neodon-gui-live --collect \
  --setenv=XDG_RUNTIME_DIR=/run/user/1000 \
  --setenv=DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus \
  --setenv=WAYLAND_DISPLAY=wayland-0 --setenv=DISPLAY=:0 \
  --setenv=QT_QPA_PLATFORMTHEME=kde \
  /usr/bin/python3 "$NEODON_APP" >/dev/null 2>&1
sleep 6
echo "GUI: $(pgrep -af 'AI/neodon-vpn/neodon-vpn.py' | head -1)"

export NEODON_LIVE=1
export NEODON_ALLOW_DISRUPTIVE=1
export NEODON_ALLOW_FIREWALL=1
export NEODON_ALLOW_UI_INPUT=1
export NEODON_WORKING_SERVER=0

echo "=== live matrix ==="
timeout 3000 bash "$QA/qa/run-all.sh" --live 2>&1 | tail -120
echo "=== rc=$? ==="
echo
echo "=== report ==="
cat "$QA/qa-results/report.md" 2>/dev/null | head -80
