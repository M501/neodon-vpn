#!/bin/bash
# One-shot: sing-box CPU (5s avg) + system power under VPN load.
P=$(pgrep -f "sing-box" | head -n 1)
echo "SINGBOX_PID=$P"
if [ -n "$P" ]; then
  A1=$(awk '{print $14+$15}' /proc/$P/stat)
  sleep 5
  A2=$(awk '{print $14+$15}' /proc/$P/stat)
  echo "SINGBOX_UTIME_DELTA=$((A2 - A1)) ticks/5s (~$(( (A2 - A1) * 100 / 500 ))% of 1 core)"
  ps -o pcpu,pmem,etime,args -p $P | tail -n 1
fi
echo "POWER_NOW=$(cat /sys/class/power_supply/BAT0/power_now 2>/dev/null) uW"
echo "BAT_STATUS=$(cat /sys/class/power_supply/BAT0/status 2>/dev/null)"
echo "VPN=$(bash ~/AI/singbox/singbox-toggle.sh status-json 2>/dev/null | python3 -c 'import json,sys; d=json.load(sys.stdin); print(d["actual_state"], d.get("exit_ip"))')"
