#!/bin/bash
# One-shot: store API with/without X-Decky-Version header + install @decky/api.
echo "== no header =="
curl -s -m 15 -o /tmp/s1.json -w "HTTP:%{http_code} SIZE:%{size_download}\n" "https://plugins.deckbrew.xyz/plugins"
echo "== with 3.2.8 header =="
curl -s -m 15 -o /tmp/s2.json -H "X-Decky-Version: v3.2.8" -w "HTTP:%{http_code} SIZE:%{size_download}\n" "https://plugins.deckbrew.xyz/plugins"
python3 -c "import json;a=json.load(open('/tmp/s1.json'));b=json.load(open('/tmp/s2.json'));print('no-hdr:',len(a),'with-hdr:',len(b))"
echo "== decky api =="
export PATH=/home/linuxbrew/.linuxbrew/bin:$PATH
cd /tmp/decky-build && npm install --no-audit --no-fund @decky/api 2>&1 | tail -n 2
ls node_modules/@decky/
