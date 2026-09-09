#!/bin/bash
# One-shot: probe Decky :1337 frontend server.
for u in /frontend/index.js /frontend/chunk-B1E4s6v6.js /frontend/; do
  code=$(curl -s -m 8 -o /tmp/decky-probe.bin -w "%{http_code}:%{size_download}" "http://127.0.0.1:1337$u" 2>/dev/null)
  echo "$u -> $code"
done
head -c 120 /tmp/decky-probe.bin 2>/dev/null; echo
