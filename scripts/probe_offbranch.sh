#!/bin/bash
# One-shot: show set_mode + off branch of live toggle script.
grep -n "MODE_FILE=" ~/AI/singbox/singbox-toggle.sh | head -n 4
echo "---SETMODE---"
awk '/^set_mode\(\)/,/^}/' ~/AI/singbox/singbox-toggle.sh | head -n 20
echo "---OFF---"
grep -n "off)" ~/AI/singbox/singbox-toggle.sh | head -n 4
