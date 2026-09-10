#!/bin/bash
# One-shot: live Steam TCP conns + routes + egress check.
echo "== steam conns =="
ss -tnp 2>/dev/null | grep -E "steam|webhelper" | awk "{print \$5}" | sort | uniq -c | sort -rn | head -n 12
echo "== cloudflare conns (any proc) =="
ss -tn 2>/dev/null | grep -E "104.21.|172.67.|162.159." | head -n 8
echo "== routes =="
ip route show default
ip -6 route show default 2>/dev/null
echo "== egress =="
curl -s -m 10 https://ifconfig.me 2>&1
echo
