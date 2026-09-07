#!/bin/bash
# Live spot-check: curl 3 domains via TUN, attribute egress via sing-box journal.
LOG=/tmp/spot-measure.log
: > "$LOG"
stamp() { date +%T.%N | cut -c1-12; }
T0=$(date +%s)
for D in rutracker.org youtube.com ya.ru; do
  IP=$(getent ahostsv4 "$D" 2>/dev/null | awk '{print $1; exit}')
  s=$(date +%s%N); C=$(curl -s -m 8 -o /dev/null -w "%{http_code}" "https://$D" 2>/dev/null); MS=$(( ($(date +%s%N) - s) / 1000000 ))
  echo "--- $(stamp) $D ip=$IP curl=$C ${MS}ms" >> "$LOG"
done
echo "--- journal since $T0 for those IPs:" >> "$LOG"
journalctl --user -u sing-box.service --since "@$T0" --no-pager 2>/dev/null | grep -iE 'outbound|proxy|direct' | tail -n 12 >> "$LOG"
echo DONE >> "$LOG"
