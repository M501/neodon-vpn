#!/bin/bash
# Re-arm the work sleep guard (PowerDevil suspends via 'sleep', keeper only blocks 'idle')
# and dump what the watchdog actually probed during the last connect attempts.
set -u
export XDG_RUNTIME_DIR=/run/user/1000
export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus
SB=/home/m26/AI/singbox

systemd-run --user --unit=hermes-sleep-hold --collect \
  /usr/bin/systemd-inhibit --what=sleep:idle --mode=block --why="hermes spec work" \
  /usr/bin/sleep 7200 >/dev/null 2>&1
sleep 1
echo "guard: $(systemctl --user is-active hermes-sleep-hold.service)"
systemd-inhibit --list 2>/dev/null | grep -c 'hermes spec work'

echo
echo "=== suspend history (boot) ==="
journalctl -b --no-pager 2>/dev/null | grep -cE "PM: suspend entry"
sudo -n journalctl -b --no-pager 2>/dev/null | grep -E "suspend requested|PM: suspend entry|PM: suspend exit" | tail -12

echo
echo "=== watchdog script ==="
ls -la "$SB/neodon-watchdog.sh"
sed -n '1,60p' "$SB/neodon-watchdog.sh"

echo
echo "=== watchdog log / state files ==="
ls -la "$SB"/.watchdog* "$SB"/watchdog* 2>/dev/null
cat "$SB/watchdog-state.json" 2>/dev/null
echo
cat /home/m26/AI/neodon-vpn/watchdog.log 2>/dev/null | tail -20 || echo "(no watchdog.log)"
