#!/bin/bash
# One-shot: libinput as root (can open devices) while qa-key presses F12.
export XDG_RUNTIME_DIR=/run/user/1000
sudo -n timeout 14 libinput debug-events --show-keycodes >/tmp/libinput-root.log 2>&1 &
sleep 3
python3 /tmp/qa-key.py 88
sleep 4
grep -iE "neodon-qa-key" /tmp/libinput-root.log | head -n 3
grep -c "KEY_F12" /tmp/libinput-root.log
