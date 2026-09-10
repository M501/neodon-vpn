#!/bin/bash
# One-shot: verify uinput keypress reaches libinput (seat level).
export XDG_RUNTIME_DIR=/run/user/1000
timeout 12 libinput debug-events --show-keycodes >/tmp/libinput.log 2>&1 &
sleep 2
python3 /tmp/qa-key.py 88
sleep 3
grep -iE "neodon-qa-key|KEY_F12" /tmp/libinput.log | head -n 6
echo "---tail---"
tail -n 4 /tmp/libinput.log
