#!/bin/bash
# Stage 3: does the highlight follow the persisted selection (external switch, VPN off)?
set -u
export XDG_RUNTIME_DIR=/run/user/1000
export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus
export WAYLAND_DISPLAY=wayland-0
export DISPLAY=:0
HOOK=/home/m26/AI/neodon-vpn/gui-action.json
SS=/home/m26/AI/singbox/singbox-server.sh

grab() {
  rm -f "$1"
  printf '%s' "{\"action\":\"grab\",\"path\":\"$1\"}" > "$HOOK"
  sleep 3
  [ -s "$1" ] && echo "grab ok: $1" || echo "GRAB FAILED: $1"
}

ORIG=$(python3 /tmp/selidx.py | head -1 | sed 's/.*index=\(-\?[0-9]*\).*/\1/')
echo "original selection index = $ORIG"

echo "########## STEP A: current (should be highlighted) ##########"
python3 /tmp/selidx.py
grab /home/m26/h1.png
python3 /tmp/frame.py /home/m26/h1.png | tail -3

for pair in "2:B" "1:C"; do
  IDX=${pair%%:*}; LBL=${pair##*:}
  echo "########## STEP $LBL: set $IDX (VPN off -> selection only) ##########"
  bash "$SS" set "$IDX" | tail -2
  sleep 9
  python3 /tmp/selidx.py
  grab "/home/m26/h_$IDX.png"
  python3 /tmp/frame.py "/home/m26/h_$IDX.png" | tail -3
done

echo "########## STEP D: restore original ($ORIG) ##########"
bash "$SS" set "$ORIG" | tail -2
sleep 9
python3 /tmp/selidx.py
grab /home/m26/h_restored.png
python3 /tmp/frame.py /home/m26/h_restored.png | tail -3

echo "########## mode/state (nothing must be powered on) ##########"
cat /home/m26/AI/singbox/.mode
systemctl --user is-active sing-box.service sing-box-full.service sing-box-proxy.service 2>&1 | tr '\n' ' '
echo
