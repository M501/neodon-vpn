#!/bin/bash
# One-shot: launch Firefox headless in bg, snapshot its sockets while hanging.
rm -rf /tmp/ffprof && mkdir -p /tmp/ffprof
flatpak run --branch=stable --arch=x86_64 org.mozilla.firefox --headless --profile /tmp/ffprof --screenshot /tmp/db.png "https://plugins.deckbrew.xyz/plugins?per_page=1" >/tmp/ff.log 2>&1 &
FFPID=$!
sleep 12
echo "== sockets =="
ss -tnp 2>/dev/null | grep -E "firefox|bwrap" | head -n 12
echo "== conntrack SYN to cloudflare =="
cat /proc/net/nf_conntrack 2>/dev/null | grep -E "SYN_SENT" | head -n 6
echo "== ff log =="
tail -n 5 /tmp/ff.log
kill $FFPID 2>/dev/null
pkill -f "firefox.*headless" 2>/dev/null
echo DONE
