#!/bin/bash
# One-shot: deploy decky main.py (active=server) + dist (dropdown, no snap-back).
cp /tmp/decky-main.py ~/homebrew/plugins/neodon-vpn/main.py
cp /tmp/decky-build/dist/index.js ~/homebrew/plugins/neodon-vpn/dist/index.js
sudo -n systemctl restart plugin_loader
sleep 25
curl -s -m 8 -o /tmp/plug6.bin -w "DIST:%{http_code}:%{size_download}\n" http://127.0.0.1:1337/plugins/neodon-vpn/dist/index.js 2>/dev/null
journalctl -u plugin_loader --no-pager --since "1 min ago" 2>&1 | grep -iE "Loaded neodon|backend up|KeyError|traceback" | head -n 4
