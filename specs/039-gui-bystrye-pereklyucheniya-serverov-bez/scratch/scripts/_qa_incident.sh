#!/bin/bash
# What actually happened during the owner's incident? (app + backend + watchdog logs)
set -u
export XDG_RUNTIME_DIR=/run/user/1000
export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus
SB=/home/m26/AI/singbox

echo "=== NOW: mode / units / exit ip ==="
cat "$SB/.mode" 2>/dev/null
systemctl --user is-active sing-box.service sing-box-full.service sing-box-proxy.service 2>&1 | tr '\n' ' '
echo
echo "connected-since: $(cat "$SB/.connected-since" 2>/dev/null || echo none)"
echo "desired: $(cat "$HOME/.desired" 2>/dev/null || echo none)"
echo "watchdog state: $(cat "$SB/watchdog-state.json" 2>/dev/null || echo none)"
echo "watchdog fails: $(cat "$SB/.watchdog-fails" 2>/dev/null || echo none)"
echo "transitioning marker: $(ls "$SB/.transitioning" 2>/dev/null || echo none)"
echo "exit ip (bare): $(curl -s -m 8 https://api.ipify.org 2>/dev/null || echo FAIL)"
echo

echo "=== transitions.log (GUI state changes, tail 40) ==="
tail -40 /home/m26/AI/neodon-vpn/transitions.log 2>/dev/null || echo "(no file)"
echo

echo "=== status-json right now ==="
timeout 20 bash "$SB/singbox-toggle.sh" status-json 2>&1 | tail -3
echo

echo "=== journal user: watchdog/neodon (last 60 min) ==="
journalctl --user --since "-60min" --no-pager 2>/dev/null | grep -iE "watchdog|internet dead|transitioning|neodon" | tail -40
echo

echo "=== journal system (last 60 min, filtered) ==="
sudo -n journalctl --since "-60min" --no-pager 2>/dev/null | grep -iE "neodon|sing-box|watchdog|suspend|firewall|tun0" | tail -25
