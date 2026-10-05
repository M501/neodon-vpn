#!/bin/bash
cd /home/m26 || exit 1
echo "PAIR before -> after_horizontal_right"
python3 /tmp/shift2.py g_before.png g_after_h.png 2>&1 | tail -2
echo "PAIR after_h -> after_h2 (swipe back left)"
python3 /tmp/shift2.py g_after_h.png g_after_h2.png 2>&1 | tail -2
echo "PAIR after_h2 -> after_vertical (control)"
python3 /tmp/shift2.py g_after_h2.png g_after_v.png 2>&1 | tail -2
echo MD5S
md5sum g_*.png
