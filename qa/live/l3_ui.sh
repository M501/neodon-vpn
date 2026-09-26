#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "$0")/.." && pwd)/lib/common.sh"
IDS=(K1 K2 K3 K4 K5 K6)
if ! require_live; then for id in "${IDS[@]}"; do skip_case "$id" "NEODON_LIVE=1 not set"; done; exit 0; fi
if ! command -v spectacle >/dev/null 2>&1; then for id in "${IDS[@]}"; do skip_case "$id" "spectacle unavailable"; done; exit 0; fi

SHOT="$RESULTS_DIR/neodon-ui.png"
case_K1() {
  XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}" \
  DBUS_SESSION_BUS_ADDRESS="${DBUS_SESSION_BUS_ADDRESS:-unix:path=/run/user/$(id -u)/bus}" \
  WAYLAND_DISPLAY="${WAYLAND_DISPLAY:-wayland-0}" \
  spectacle -b -n -o "$SHOT" >/dev/null
  [[ -s "$SHOT" ]]
}
case_K2() {
  # prerequisites: unlocked session + CONNECTED (blue checked power button only then)
  SID="$(loginctl list-sessions --no-legend 2>/dev/null | awk -v u="$USER" '$3==u{print $1; exit}')"
  if [ -n "${SID:-}" ] && [ "$(loginctl show-session "$SID" -p LockedHint 2>/dev/null)" = "LockedHint=yes" ]; then return 77; fi
  ST="$(bash "$BACKEND_ROOT/singbox-toggle.sh" status-json 2>/dev/null | python3 -c 'import json,sys;print(json.load(sys.stdin).get("actual_state",""))' 2>/dev/null || true)"
  [ "$ST" = "CONNECTED" ] || return 77
  python3 - "$SHOT" <<'PY'
from PIL import Image
import sys
img=Image.open(sys.argv[1]).convert('RGB')
# Look for the documented blue power-button fill. This is a presence/sanity check, not a pixel-perfect oracle.
target=(42,95,216)
count=0
for r,g,b in img.resize((min(img.width,1200), min(img.height,700))).getdata():
    if abs(r-target[0])<12 and abs(g-target[1])<12 and abs(b-target[2])<12:
        count += 1
assert count > 200, count
PY
}
case_K3() { python3 -c 'from PIL import Image; import sys; im=Image.open(sys.argv[1]); assert im.width>=1 and im.height>=1' "$SHOT"; }
case_K4() { return 77; } # OS notification count needs notification-daemon instrumentation
case_K5() { return 77; } # sidebar navigation needs stable Qt object/page hooks
case_K6() { return 77; } # singleton launch needs exact desktop/autostart control
for id in "${IDS[@]}"; do run_case "$id" "case_$id"; done
