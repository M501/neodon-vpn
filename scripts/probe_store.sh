#!/bin/bash
# One-shot: probe Decky store API reachability from host.
curl -s -m 20 -o /tmp/store.json -w "STORE HTTP:%{http_code} SIZE:%{size_download} TIME:%{time_total}s\n" "https://plugins.deckbrew.xyz/plugins"
head -c 300 /tmp/store.json 2>/dev/null
echo
curl -s -m 15 -o /dev/null -w "ROOT HTTP:%{http_code} TIME:%{time_total}s\n" https://plugins.deckbrew.xyz/ 2>&1
# DNS + SNI sanity
getent hosts plugins.deckbrew.xyz || nslookup plugins.deckbrew.xyz 2>&1 | tail -n 3
