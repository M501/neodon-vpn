#!/bin/bash
# Deep QA battery (detached): FULL mode under traffic, soak of reconnects, Wi-Fi loss,
# suspend/resume via an RTC alarm. Everything is logged; the script never leaves the
# device in a non-canonical state (ends with mode=off) and re-arms the sleep guard.
set -u
export XDG_RUNTIME_DIR=/run/user/1000
export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus
export WAYLAND_DISPLAY=wayland-0 DISPLAY=:0
SB=/home/m26/AI/singbox
LOG=/home/m26/deep_qa.log
: > "$LOG"

say() { echo "[$(date +%H:%M:%S)] $*" | tee -a "$LOG"; }
sjson() { timeout 30 bash "$SB/singbox-toggle.sh" status-json 2>/dev/null | tail -1; }
state() { sjson | python3 -c 'import json,sys
try: print(json.load(sys.stdin).get("actual_state"))
except Exception: print("?")' 2>/dev/null; }
guarded() { systemd-run --user --unit=hermes-sleep-hold --collect \
  /usr/bin/systemd-inhibit --what=sleep:idle --mode=block --why="hermes spec work" \
  /usr/bin/sleep 7200 >/dev/null 2>&1; }

say "=== A) FULL (TUNNEL) under real traffic ==="
bash "$SB/singbox-toggle.sh" full >/dev/null 2>&1; say "full rc=$?"
for i in 1 2 3 4 5 6; do sleep 5; say "A state=$(state) exit=$(curl -s -m 6 https://api.ipify.org 2>/dev/null || echo FAIL)"; done
say "A tun0=$(ip link show tun0 2>/dev/null | grep -c UP) ip-rule=$(ip rule show 2>/dev/null | grep -c 2022)"
for u in https://ya.ru https://www.google.com https://api.ipify.org https://github.com; do
  code=$(curl -s -m 8 -o /dev/null -w '%{http_code}' "$u" 2>/dev/null || echo 000)
  say "A http $u -> $code"
done
say "A quota-guard: $(systemctl --user is-active neodon-tunnel-guard.service 2>&1) / timer $(systemctl --user is-active neodon-tunnel-guard.timer 2>&1)"
say "A 60s idle soak in full..."
sleep 60
say "A after soak: state=$(state) exit=$(curl -s -m 8 https://api.ipify.org 2>/dev/null || echo FAIL)"
bash "$SB/singbox-toggle.sh" smart >/dev/null 2>&1; sleep 10
say "A back to smart: state=$(state)"

say "=== B) soak: 6 reconnect cycles (off -> smart) ==="
for i in 1 2 3 4 5 6; do
  bash "$SB/singbox-toggle.sh" off >/dev/null 2>&1; sleep 4
  bash "$SB/singbox-toggle.sh" smart >/dev/null 2>&1; sleep 12
  say "B cycle $i: state=$(state) exit=$(curl -s -m 8 https://api.ipify.org 2>/dev/null || echo FAIL) rules20=$(sudo -n firewall-cmd --direct --get-all-rules 2>/dev/null | grep -c 'OUTPUT_direct 20 ')"
done
say "B workers/mem: gui_rss=$(ps -o rss= -p "$(pgrep -f 'AI/neodon-vpn/neodon-vpn.py' | head -1)" 2>/dev/null | tr -d ' ') kB, procs=$(pgrep -cf 'neodon-vpn.py')"

say "=== C) Wi-Fi loss while the tunnel is up (NM-guard must not kill the VPN) ==="
bash "$SB/singbox-toggle.sh" smart >/dev/null 2>&1; sleep 12
say "C before: mode=$(cat "$SB/.mode") state=$(state)"
nmcli device disconnect wlan0 >/dev/null 2>&1; say "C wlan0 disconnected (SSH will drop)"
sleep 30
say "C during outage: mode=$(cat "$SB/.mode") state=$(state) watchdog=$(cat "$SB/.watchdog-fails" 2>/dev/null || echo none)"
nmcli device connect wlan0 >/dev/null 2>&1; say "C wlan0 reconnecting"
for i in 1 2 3 4 5 6; do sleep 10; say "C restore $i: state=$(state) exit=$(curl -s -m 8 https://api.ipify.org 2>/dev/null || echo FAIL)"; done
say "C transitions tail: $(tail -3 /home/m26/AI/neodon-vpn/transitions.log | tr '\n' ' ')"

say "=== D) suspend/resume with the tunnel up (RTC wake alarm) ==="
if [ -w /sys/class/rtc/rtc0/wakealarm ] 2>/dev/null || [ -r /sys/class/rtc/rtc0/wakealarm ] 2>/dev/null; then
  bash "$SB/singbox-toggle.sh" smart >/dev/null 2>&1; sleep 12
  say "D before: mode=$(cat "$SB/.mode") state=$(state) exit=$(curl -s -m 8 https://api.ipify.org 2>/dev/null || echo FAIL)"
  guarded
  systemctl --user stop hermes-sleep-hold.service 2>/dev/null   # allow the suspend
  sleep 1
  say "D sleeping via rtcwake (alarm +150s)..."
  rtcwake -m mem -s 150 >>"$LOG" 2>&1 || say "D rtcwake rc=$? (wake may need a manual button)"
  sleep 10
  say "D after wake: mode=$(cat "$SB/.mode") state=$(state) exit=$(curl -s -m 10 https://api.ipify.org 2>/dev/null || echo FAIL)"
  for i in 1 2 3; do sleep 10; say "D settle $i: state=$(state) exit=$(curl -s -m 8 https://api.ipify.org 2>/dev/null || echo FAIL)"; done
  say "D transitions tail: $(tail -4 /home/m26/AI/neodon-vpn/transitions.log | tr '\n' ' ')"
else
  say "D SKIP: no RTC wakealarm support (suspend test needs a physical wake)"
fi

say "=== E) canonical state: OFF + clean checks ==="
bash "$SB/singbox-toggle.sh" off >/dev/null 2>&1; sleep 6
say "E mode=$(cat "$SB/.mode") units=$(systemctl --user is-active sing-box.service sing-box-full.service sing-box-proxy.service 2>&1 | tr '\n' ' ')"
say "E rules20=$(sudo -n firewall-cmd --direct --get-all-rules 2>/dev/null | grep -c 'OUTPUT_direct 20 ') resolv=$(head -1 /etc/resolv.conf)"
say "E internet=$(curl -s -m 8 https://api.ipify.org 2>/dev/null || echo FAIL) gui=$(pgrep -cf 'AI/neodon-vpn/neodon-vpn.py')"
guarded
say "E guard=$(systemctl --user is-active hermes-sleep-hold.service)"
say "DEEP_QA_DONE"
