#!/bin/bash
# QA backdoor shot: navigate to a page via ACTION_HOOK, spectacle it.
PAGE="${1:-servers}"
OUT="/home/m26/shot-$PAGE.png"
echo "{\"action\": \"navigate\", \"page\": \"$PAGE\"}" > ~/AI/neodon-vpn/gui-action.json
sleep 2
export XDG_RUNTIME_DIR=/run/user/1000 WAYLAND_DISPLAY=wayland-0
spectacle -b -n -o "$OUT" 2>&1 | head -n 2
ls -la "$OUT"
