#!/bin/bash
# One-shot: resolve all deckbrew A records, probe EACH via --resolve.
echo "== all A records =="
for i in 1 2 3 4 5 6; do nslookup plugins.deckbrew.xyz 2>/dev/null | awk "/^Address: /{print \$2}"; done | sort -u
echo "== per-IP probe =="
for ip in $(for i in 1 2 3; do nslookup plugins.deckbrew.xyz 2>/dev/null | awk "/^Address: /{print \$2}"; done | sort -u); do
  code=$(curl -s -m 10 -o /dev/null --resolve plugins.deckbrew.xyz:443:$ip -w "%{http_code}:%{time_total}s" "https://plugins.deckbrew.xyz/plugins?per_page=1" 2>&1)
  echo "$ip -> $code"
done
