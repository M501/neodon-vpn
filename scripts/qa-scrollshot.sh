#!/bin/bash
# QA: scroll current page by N px via ACTION_HOOK, then spectacle shot.
BY="${1:-500}"
NAME="${2:-shot-scroll}"
OUT="/home/m26/$NAME.png"
python3 -c "import json; json.dump({'action': 'scroll', 'by': int($BY)}, open('/home/m26/AI/neodon-vpn/gui-action.json', 'w'))"
sleep 2
export XDG_RUNTIME_DIR=/run/user/1000 WAYLAND_DISPLAY=wayland-0
spectacle -b -n -o "$OUT" 2>&1 | head -n 2
ls -la "$OUT"
