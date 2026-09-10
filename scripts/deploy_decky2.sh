#!/bin/bash
# One-shot: deploy decky dist, restart loader, verify backend+serving.
cp /tmp/decky-build/dist/index.js ~/homebrew/plugins/neodon-vpn/dist/index.js
grep -c "refresh_sub" ~/homebrew/plugins/neodon-vpn/main.py
sudo -n systemctl restart plugin_loader
sleep 25
curl -s -m 8 -o /tmp/plug4.bin -w "DIST:%{http_code}:%{size_download}\n" http://127.0.0.1:1337/plugins/neodon-vpn/dist/index.js 2>/dev/null
grep -c "refresh_sub\|servers + traffic" /tmp/plug4.bin
journalctl -u plugin_loader --no-pager --since "1 min ago" 2>&1 | grep -iE "neodon|KeyError|traceback" | head -n 6
