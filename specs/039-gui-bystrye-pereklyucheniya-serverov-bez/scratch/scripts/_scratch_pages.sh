#!/bin/bash
# Post-cleanup sanity: every page still renders (no dead-widget crashes).
set -u
export XDG_RUNTIME_DIR=/run/user/1000
export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus
export WAYLAND_DISPLAY=wayland-0
export DISPLAY=:0
HOOK=/home/m26/AI/neodon-vpn/gui-action.json

nav() { printf '{"action":"navigate","page":"%s"}' "$1" > "$HOOK"; sleep 2; }
grab() { rm -f "$1"; printf '{"action":"grab","path":"%s"}' "$1" > "$HOOK"; sleep 2.5; [ -s "$1" ] && echo "ok $1 ($(stat -c%s "$1") bytes)" || echo "FAIL $1"; }

for pg in settings apps traffic logs about home; do
  nav "$pg"
  grab "/home/m26/pg_$pg.png"
done
echo "--- gui process alive? ---"
pgrep -af "AI/neodon-vpn/neodon-vpn.py" | head -1
echo "--- recent GUI stderr (unit log) ---"
journalctl --user -u neodon-gui-live --no-pager -n 15 2>/dev/null | tail -12
