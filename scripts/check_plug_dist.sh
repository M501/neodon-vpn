#!/bin/bash
# One-shot: probe Decky plugin dist URLs served on :1337.
for u in /plugins/neodon-vpn/dist/index.js /plugins/neodon-vpn/index.js /neodon-vpn/dist/index.js; do
  code=$(curl -s -m 8 -o /tmp/plug-probe.bin -w "%{http_code}:%{size_download}" "http://127.0.0.1:1337$u" 2>/dev/null)
  echo "$u -> $code"
done
grep -c "servers + traffic" /tmp/plug-probe.bin 2>/dev/null || true
