#!/bin/bash
# Where do post-restart seconds go: SOCKS listen vs first working exit?
LOG=/tmp/listen-measure.log
: > "$LOG"
stamp() { date +%T.%N | cut -c1-12; }
echo "=== $(stamp) restart proxy" >> "$LOG"
systemctl --user restart sing-box-proxy.service
echo "=== $(stamp) restarted, wait listen 10808" >> "$LOG"
for i in $(seq 1 60); do
  if ss -ltn 2>/dev/null | grep -q 10808; then echo "=== $(stamp) LISTEN after ~$((i * 2))00ms" >> "$LOG"; break; fi
  sleep 0.2
done
echo "=== $(stamp) curl loop -m 1 via socks" >> "$LOG"
for i in $(seq 1 15); do
  IP=$(curl -s -m 1 -x socks5h://127.0.0.1:10808 https://api.ipify.org 2>/dev/null)
  echo "--- $(stamp) try $i: ${IP:-FAIL}" >> "$LOG"
  [ -n "$IP" ] && break
  sleep 1
done
echo DONE >> "$LOG"
