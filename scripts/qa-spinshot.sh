#!/bin/bash
# QA: park on the Ping/refresh row, then trigger refresh, shoot fast.
python3 -c "import json; json.dump({'action': 'scroll', 'by': 250}, open('/home/m26/AI/neodon-vpn/gui-action.json', 'w'))"
sleep 2
python3 -c "import json; json.dump({'action': 'refresh'}, open('/home/m26/AI/neodon-vpn/gui-action.json', 'w'))"
sleep 1
export XDG_RUNTIME_DIR=/run/user/1000 WAYLAND_DISPLAY=wayland-0
spectacle -b -n -o /home/m26/shot-spin.png 2>&1 | head -n 2
ls -la /home/m26/shot-spin.png
