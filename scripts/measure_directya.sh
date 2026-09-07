#!/bin/bash
# Direct-path A/B for yandex: TUN-direct vs wlan-direct vs proxy.
LOG=/tmp/directya-measure.log
: > "$LOG"
stamp() { date +%T.%N | cut -c1-12; }
PHY=$(ip route show default 2>/dev/null | head -n 1 | cut -d" " -f5)
echo "=== $(stamp) PHY=$PHY mode=$(cat ~/AI/singbox/.mode)" >> "$LOG"
s=$(date +%s%N); W=$(curl -s -4 -m 6 --interface "$PHY" -o /dev/null -w "%{http_code}" https://ya.ru 2>/dev/null); echo "--- $(stamp) wlan-direct-ya: $W $(( ($(date +%s%N) - s) / 1000000 ))ms" >> "$LOG"
s=$(date +%s%N); W=$(curl -s -4 -m 6 --interface "$PHY" -o /dev/null -w "%{http_code}" https://yandex.ru 2>/dev/null); echo "--- $(stamp) wlan-direct-yandex: $W $(( ($(date +%s%N) - s) / 1000000 ))ms" >> "$LOG"
s=$(date +%s%N); W=$(curl -s -4 -m 6 -o /dev/null -w "%{http_code}" https://mail.ru 2>/dev/null); echo "--- $(stamp) tun-mail: $W $(( ($(date +%s%N) - s) / 1000000 ))ms" >> "$LOG"
echo DONE >> "$LOG"
