#!/bin/bash
# QA: refresh, then scroll to servers, screenshot mid-flight.
python3 -c "import json; json.dump({'action': 'refresh'}, open('/home/m26/AI/neodon-vpn/gui-action.json', 'w'))"
sleep 1
python3 -c "import json; json.dump({'action': 'scroll', 'by': 700}, open('/home/m26/AI/neodon-vpn/gui-action.json', 'w'))"
sleep 2
export XDG_RUNTIME_DIR=/run/user/1000 WAYLAND_DISPLAY=wayland-0
spectacle -b -n -o /home/m26/shot-refresh2.png 2>&1 | head -n 2
ls -la /home/m26/shot-refresh2.png
