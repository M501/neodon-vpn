#!/bin/bash
# Prove the sleep guard actually blocks a suspend request, and show who woke/slept.
set -u
export XDG_RUNTIME_DIR=/run/user/1000
export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus

echo "=== inhibitors (hermes) ==="
systemd-inhibit --list 2>&1 | grep -i hermes

echo "=== CanSuspend / CanHibernate ==="
busctl call org.freedesktop.login1 /org/freedesktop/login1 \
  org.freedesktop.login1.Manager CanSuspend 2>&1

echo "=== what requested the 20:19 suspend ==="
journalctl -b --no-pager -o short-precise 2>/dev/null | grep -n -B6 "The system will suspend now" | tail -30

echo "=== powerdevil: is it running / what timeouts ==="
systemctl --user is-active plasma-powerdevil.service 2>&1
kreadconfig6 --file powerdevilrc --group Battery --group SuspendSession --key timeout 2>&1
kreadconfig6 --file powerdevilrc --group AC --group SuspendSession --key timeout 2>&1
kreadconfig6 --file powermanagementprofilesrc --group Battery --group SuspendSession --key idleTime 2>&1
echo "--- battery profile block in powerdevilrc ---"
grep -n -A4 "\[Battery\]" /home/m26/.config/powerdevilrc 2>&1 | head -30
echo "--- AC block ---"
grep -n -A4 "\[AC\]" /home/m26/.config/powerdevilrc 2>&1 | head -30
