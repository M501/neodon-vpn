#!/bin/bash
# One-shot: persistent uinput kbd + evtest capture on its node.
python3 /tmp/qa-keyhold.py >/tmp/keyhold.log 2>&1 &
sleep 2
NODE=""
for ev in /sys/class/input/event*; do
  if grep -q "neodon-qa-keyhold" $ev/device/name 2>/dev/null; then
    NODE="/dev/input/$(basename $ev)"
  fi
done
echo "NODE=$NODE"
if [ -n "$NODE" ]; then
  sudo -n timeout 14 evtest "$NODE" 2>&1 | grep -E "KEY_F12|SYN_REPORT" | head -n 12
fi
wait
