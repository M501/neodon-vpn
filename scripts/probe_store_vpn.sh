#!/bin/bash
# One-shot: store via direct vs via VPN egress + decky store setting.
echo "== VPN state =="
bash ~/AI/singbox/singbox-toggle.sh status-json 2>/dev/null | head -c 400
echo
echo "== direct =="
curl -s -m 15 -o /dev/null -w "DIRECT HTTP:%{http_code} TIME:%{time_total}s\n" "https://plugins.deckbrew.xyz/plugins?per_page=1"
echo "== via socks (if proxy up) =="
curl -s -m 15 -o /dev/null -x socks5h://127.0.0.1:2080 -w "SOCKS HTTP:%{http_code} TIME:%{time_total}s\n" "https://plugins.deckbrew.xyz/plugins?per_page=1" 2>&1
echo "== decky settings =="
ls ~/homebrew/settings/ 2>/dev/null
grep -ri "store" ~/homebrew/settings/ 2>/dev/null | head -n 5
