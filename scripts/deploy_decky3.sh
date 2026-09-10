#!/bin/bash
# One-shot: deploy decky dist (stepper+profile), restart loader, verify.
cp /tmp/decky-build/dist/index.js ~/homebrew/plugins/neodon-vpn/dist/index.js
sudo -n systemctl restart plugin_loader
sleep 25
curl -s -m 8 -o /tmp/plug5.bin -w "DIST:%{http_code}:%{size_download}\n" http://127.0.0.1:1337/plugins/neodon-vpn/dist/index.js 2>/dev/null
grep -c "stepServer\|set_server" /tmp/plug5.bin
journalctl -u plugin_loader --no-pager --since "1 min ago" 2>&1 | grep -iE "Loaded neodon|backend up|KeyError|traceback" | head -n 4
