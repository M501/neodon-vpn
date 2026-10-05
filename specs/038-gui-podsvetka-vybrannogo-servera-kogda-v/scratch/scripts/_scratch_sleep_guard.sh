#!/bin/bash
# Sleep-hazard triage + arm a TTL-guarded sleep block for the work window.
set -u
export XDG_RUNTIME_DIR=/run/user/1000
export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus

echo "=== power source ==="
for f in /sys/class/power_supply/AC*/online /sys/class/power_supply/AC*/{online,type}; do
  [ -r "$f" ] && echo "$f = $(cat "$f")"
done
grep -l . /sys/class/power_supply/*/online 2>/dev/null | while read -r p; do echo "$p = $(cat "$p")"; done
echo "battery: $(cat /sys/class/power_supply/BAT0/capacity 2>/dev/null)% status=$(cat /sys/class/power_supply/BAT0/status 2>/dev/null)"

echo "=== recent suspend/reboot ==="
journalctl -b --no-pager 2>/dev/null | grep -iE "PM: suspend|suspend entry|system will suspend|The system will suspend" | tail -6 || echo "(journal needs root?)"

echo "=== inhibitors now ==="
systemd-inhibit --list 2>&1 | tail -12

echo "=== remote-keeper ==="
ls -la /home/m26/.local/bin/remote-keeper.sh 2>&1
systemctl --user is-enabled remote-keeper.timer remote-keeper.service 2>&1 | head -4
bash /home/m26/.local/bin/remote-keeper.sh status 2>&1 | tail -8 || echo "keeper status rc=$?"

echo "=== powerdevil idle policy ==="
for g in AC Battery; do
  echo "-- $g"
  kreadconfig6 --file powerdevilrc --group "$g" --group SuspendSession --key timeout 2>/dev/null || echo "(no powerdevilrc group)"
  kreadconfig6 --file powerdevilrc --group "$g" --group SuspendSession --key suspendType 2>/dev/null
  kreadconfig6 --file powerdevilrc --group "$g" --group DimDisplay --key idleTime 2>/dev/null
  kreadconfig6 --file powerdevilrc --group "$g" --group TurnOffDisplay --key idleTime 2>/dev/null
done
echo "-- raw powerdevilrc --"
sed -n '1,60p' /home/m26/.config/powerdevilrc 2>&1

echo "=== arm guard ==="
if systemctl --user is-active hermes-work-guard.service >/dev/null 2>&1; then
  echo "guard already active"
else
  systemd-run --user --unit=hermes-work-guard --collect \
    /usr/bin/systemd-inhibit --what=sleep:idle --mode=block --why="hermes remote work" \
    /usr/bin/sleep 7200 >/dev/null 2>&1
  sleep 1
  echo "guard started rc=$?"
fi
systemctl --user is-active hermes-work-guard.service
systemd-inhibit --list 2>&1 | grep -i hermes
