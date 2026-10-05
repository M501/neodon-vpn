#!/bin/bash
cd /home/m26 || exit 1
for pair in "g_before.png g_after_h.png" "g_after_h.png g_after_h2.png" "g_after_h2.png g_after_v.png"; do
  echo "PAIR $pair"
  set -- $pair
  python3 /tmp/shift.py "$1" "$2" 2>&1 | tail -3
done
echo "MD5S:"
md5sum /home/m26/g_*.png
