#!/bin/bash
# Deploy the hardened build to the live path, restart the GUI, re-run the static suite.
set -u
export XDG_RUNTIME_DIR=/run/user/1000
export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus
export WAYLAND_DISPLAY=wayland-0 DISPLAY=:0 QT_QPA_PLATFORMTHEME=kde
QA=/home/m26/AI/neodon-qa
LIVE=/home/m26/AI/neodon-vpn/neodon-vpn.py

echo "=== deploy (backup .pre039 stays) ==="
md5sum "$LIVE" /home/m26/AI/neodon-qa/neodon-vpn.py
cp /home/m26/AI/neodon-qa/neodon-vpn.py "$LIVE"
md5sum "$LIVE"

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
  /usr/bin/python3 "$LIVE" >/dev/null 2>&1
sleep 5
echo "GUI: $(pgrep -af 'AI/neodon-vpn/neodon-vpn.py' | head -1)"

echo
echo "=== final static suite against the live file ==="
cd "$QA" || exit 1
NEODON_REPO="$QA" NEODON_APP="$LIVE" QT_QPA_PLATFORM=offscreen \
  timeout 300 python3 -m pytest -q "$QA/tests" 2>&1 | tail -4

echo
echo "=== live route sanity after deploy (toggle via hook) ==="
HOOK=/home/m26/AI/neodon-vpn/gui-action.json
printf '{"action":"toggle"}' > "$HOOK"; sleep 12
rm -f /tmp/st.json; printf '{"action":"state","path":"/tmp/st.json"}' > "$HOOK"; sleep 2
cat /tmp/st.json 2>/dev/null; echo
printf '{"action":"toggle"}' > "$HOOK"; sleep 10
rm -f /tmp/st.json; printf '{"action":"state","path":"/tmp/st.json"}' > "$HOOK"; sleep 2
cat /tmp/st.json 2>/dev/null; echo
echo "mode: $(cat /home/m26/AI/singbox/.mode)"
echo "prio-20 rules: $(sudo -n firewall-cmd --direct --get-all-rules 2>/dev/null | grep -c 'OUTPUT_direct 20 ' || true)"
echo "internet: $(curl -s -m 8 https://api.ipify.org 2>/dev/null || echo FAIL)"
