#!/bin/bash
# One-shot: check latest Decky release tag.
code=$(curl -s -m 15 -o /tmp/decky-rel.json -w "%{http_code}" https://api.github.com/SteamDeckHomebrew/decky-loader/releases/latest 2>/dev/null)
echo "HTTP-$code"
python3 -c "import json; d=json.load(open('/tmp/decky-rel.json')); print(d.get('tag_name'))" 2>&1 | head -n 2
