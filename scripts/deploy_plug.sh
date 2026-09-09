#!/bin/bash
# One-shot: deploy plugin.json, restart loader, probe dist URL + journal.
cp /tmp/decky-plugin.json ~/homebrew/plugins/neodon-vpn/plugin.json
sudo -n systemctl restart plugin_loader
sleep 25
curl -s -m 8 -o /tmp/plug2.bin -w "DIST:%{http_code}:%{size_download}\n" http://127.0.0.1:1337/plugins/neodon-vpn/dist/index.js 2>/dev/null
grep -c "servers + traffic" /tmp/plug2.bin 2>/dev/null
journalctl -u plugin_loader --no-pager --since "1 min ago" 2>&1 | grep -iE "neodon|KeyError|traceback" | head -n 6
