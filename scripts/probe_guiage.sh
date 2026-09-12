#!/bin/bash
# One-shot: is the running GUI older than the fixed file on disk?
ps -o lstart= -p 101768
echo "---"
stat -c "%y" ~/AI/neodon-vpn/neodon-vpn.py
grep -c "_tray_default" ~/AI/neodon-vpn/neodon-vpn.py
echo "---"
cat /proc/101768/cmdline 2>/dev/null | tr '\0' ' '
echo
