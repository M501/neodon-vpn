#!/bin/bash
# One-shot: time github/CDN via TUN + dump killswitch nft rules.
echo "== github api =="
curl -s -m 25 -o /dev/null -w "GITHUB HTTP:%{http_code} TIME:%{time_total}s\n" "https://api.github.com/repos/SteamDeckHomebrew/decky-loader/releases?per_page=1"
echo "== tzatzikiweeb =="
curl -s -m 25 -o /dev/null -w "CDN HTTP:%{http_code} TIME:%{time_total}s\n" "https://cdn.tzatzikiweeb.moe/file/steam-deck-homebrew/versions/"
echo "== nft (our chains) =="
sudo -n nft list ruleset 2>/dev/null | grep -iE "cgroup|socket|mark|tun0|dport \{?44" | head -n 15
