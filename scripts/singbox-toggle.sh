#!/bin/bash
# NOTE (public copy): exact home IP redacted -> 79.139.* prefix checks.
# Live host copy uses the full IP; functionally identical.
export XDG_RUNTIME_DIR=/run/user/$(id -u)
MODE_FILE=~/AI/singbox/.mode
# mutex: сериализуем переключения (гонка двух toggles давала рассинхрон .mode/сервис)
exec 9>~/AI/singbox/.toggle.lock
# read-only статусы не ждут мьютекс: иначе toggle стоит в очереди
# за медленными опросами (curl/питоны в status-json). writer'ы -
# эксклюзив, status - fail-open (читает только marker/mode/profile).
case "$1" in
  status|status-json) flock -n 9 || true ;;
  *) flock 9 ;;
esac
TRANS_MARKER=~/AI/singbox/.transitioning
notify() { notify-send "VPN" "$1" 2>/dev/null || true; }
set_mode() { echo "$1" > "$MODE_FILE"; }
wd_reset() { python3 -c 'import json,time;f="/home/m26/AI/singbox/watchdog-state.json";d=json.load(open(f));d.update({"consecutive_failures":0,"backoff_index":0,"next_due_ts":int(time.time()),"watchdog_status":"ok"});json.dump(d,open(f,"w"))'; }
fw_flush() { bash ~/AI/singbox/killswitch.sh remove >/dev/null 2>&1 || true; }
stop_all() {
  systemctl --user stop sing-box.service 2>/dev/null
  systemctl --user stop sing-box-full.service 2>/dev/null
  systemctl --user stop sing-box-proxy.service 2>/dev/null
}
case "$1" in
  smart|full|proxy|off)
    touch "$TRANS_MARKER"
    trap 'rm -f "$TRANS_MARKER"' EXIT INT TERM
    ;;
esac
case "$1" in
  smart) bash ~/AI/singbox/dns-fix.sh apply || true; bash ~/AI/neodon-flatpak/firefox-proxy.sh restore || true; stop_all; fw_flush; set_mode smart; if systemctl --user start sing-box.service; then wd_reset; echo "VPN SMART ON"; notify "VPN SMART ON"; else echo "VPN: ошибка"; notify "VPN: ошибка"; fi;;
  full)
    bash ~/AI/neodon-flatpak/firefox-proxy.sh restore || true
    stop_all
    fw_flush
    bash ~/AI/singbox/dns-fix.sh apply || true
    set_mode full
    if ! systemctl --user start sing-box-full.service; then
      echo "FULL FAILED — service start error; firewall state: $(sudo -n firewall-cmd --direct --get-all-rules 2>/dev/null | wc -l) rules; if LOCKED run 'toggle off' to unlock"
      notify "FULL FAILED — service start error (firewall LOCKED)"
      exit 1
    fi
    for i in $(seq 1 15); do
      systemctl --user is-active sing-box-full.service >/dev/null 2>&1 && break
      sleep 1
    done
    if ! systemctl --user is-active sing-box-full.service >/dev/null 2>&1; then
      echo "FULL FAILED — service not active; firewall state: $(sudo -n firewall-cmd --direct --get-all-rules 2>/dev/null | wc -l) rules; if LOCKED run 'toggle off' to unlock"
      notify "FULL FAILED — service not active (firewall LOCKED)"
      exit 1
    fi
    sleep 2
    if ! ip link show tun0 >/dev/null 2>&1; then
      echo "FULL FAILED — tun0 missing (firewall LOCKED, fail-closed). Run 'toggle off' to unlock."
      notify "FULL FAILED — no tun0 (firewall LOCKED)"
      exit 1
    fi
    if ! ip route get 1.1.1.1 2>/dev/null | grep -q tun0; then
      echo "FULL FAILED — no tun0 default route (firewall LOCKED, fail-closed). Run 'toggle off' to unlock."
      notify "FULL FAILED — no tun0 route (firewall LOCKED)"
      exit 1
    fi
    # fail-closed: киллсвитч СРАЗУ после подъёма сервиса, exit-проверка — после
    if ! bash ~/AI/singbox/killswitch.sh install >/dev/null 2>&1; then
      echo "FULL FAILED — killswitch install error; run 'toggle off' to unlock"
      notify "FULL FAILED — killswitch install error"
      exit 1
    fi
    wd_reset
    EXIT=$(curl -s -m 8 https://api.ipify.org 2>/dev/null)
    if [ -n "$EXIT" ] && [[ "$EXIT" != 79.139.* ]]; then
      echo "VPN FULL ON (READY) — exit $EXIT"
      notify "VPN FULL ON — exit $EXIT"
    else
      echo "FULL WARNING — exit не подтверждён, но firewall LOCKED (fail-closed). Run 'toggle off' to unlock."
    fi
    ;;
  proxy) stop_all; fw_flush; set_mode proxy; bash ~/AI/singbox/dns-fix.sh apply || true; if systemctl --user start sing-box-proxy.service; then wd_reset; bash ~/AI/neodon-flatpak/firefox-proxy.sh apply || true; echo "VPN PROXY ON"; notify "VPN PROXY ON"; else echo "VPN: ошибка"; notify "VPN: ошибка"; fi;;
  off)
    bash ~/AI/neodon-flatpak/firefox-proxy.sh restore || true
    stop_all
    sleep 2
    N=$(sudo -n firewall-cmd --direct --get-all-rules 2>/dev/null | wc -l)
    if [ "$N" -gt 0 ]; then
      sudo -n firewall-cmd --direct --remove-rules ipv4 filter OUTPUT_direct 2>/dev/null || true
      sudo -n firewall-cmd --direct --remove-rules ipv6 filter OUTPUT_direct 2>/dev/null || true
      echo "WARN: removed $N stuck rules"
    fi
    bash ~/AI/singbox/dns-fix.sh restore || true
    set_mode off
    echo "VPN OFF — internet via ISP"
    notify "VPN OFF — internet via ISP"
    ;;
status-json)
    desired=$(cat "$MODE_FILE" 2>/dev/null || echo unknown)
    transitioning=false
    [ -f "$TRANS_MARKER" ] && transitioning=true
    svc=sing-box.service
    case "$desired" in
      full) svc=sing-box-full.service ;;
      proxy) svc=sing-box-proxy.service ;;
    esac
    fw_rules=$(sudo -n firewall-cmd --direct --get-all-rules 2>/dev/null | wc -l)
    if ip link show tun0 >/dev/null 2>&1; then tun_up=true; else tun_up=false; fi
    exit_ip=""
    case "$desired" in
      full|smart) exit_ip=$(curl -s -m 3 https://api.ipify.org 2>/dev/null) ;;
      proxy) exit_ip=$(curl -s -m 3 -x socks5h://127.0.0.1:10808 https://api.ipify.org 2>/dev/null) ;;
    esac
    exit_ok=false
    if [ -n "$exit_ip" ]; then
      if [ "$desired" = "full" ] && [[ "$exit_ip" == 79.139.* ]]; then exit_ok=false
      else exit_ok=true; fi
    fi
    if [ "$desired" = "off" ]; then
      any_active=false
      for u in sing-box.service sing-box-full.service sing-box-proxy.service; do
        [ "$(systemctl --user is-active "$u" 2>/dev/null)" = "active" ] && any_active=true
      done
      svc=none
      if [ "$any_active" = true ]; then
        svc_state=active
        state=STOPPING
      elif [ "$fw_rules" -gt 0 ]; then
        svc_state=inactive
        state=STOPPING
      else
        svc_state=inactive
        state=OFF
      fi
    else
      svc_state=$(systemctl --user is-active "$svc" 2>/dev/null | head -1)
      [ -n "$svc_state" ] || svc_state=inactive
      substate=$(systemctl --user show -p SubState --value "$svc" 2>/dev/null)
      state=FAILED
      if [ "$transitioning" = true ]; then
        state=TRANSITIONING
      elif [ "$svc_state" = "active" ] && [ "$exit_ok" = true ]; then
        state=CONNECTED
      else
        case "$svc_state" in
          active)
            if [ "$tun_up" = true ]; then state=DEGRADED; else state=CONNECTING; fi
            ;;
          activating)
            if [ "$substate" = "auto-restart" ]; then
              if [ "$fw_rules" -gt 0 ]; then state=LOCKED; else state=FAILED; fi
            else
              state=STARTING
            fi
            ;;
          inactive|failed)
            if [ "$fw_rules" -gt 0 ]; then state=LOCKED; else state=FAILED; fi
            ;;
          *) state=FAILED ;;
        esac
      fi
    fi
    PROFILE="$(cat "$HOME/AI/singbox/.profile" 2>/dev/null || echo default)"
    read -r wd_status wd_fails wd_next < <(python3 - <<'EOF' 2>/dev/null
import json
try:
    d = json.load(open('/home/m26/AI/singbox/watchdog-state.json'))
    print(d.get('watchdog_status', ''), d.get('consecutive_failures', 0), d.get('next_due_ts') or d.get('next_retry_ts') or '')
except Exception:
    print('', 0, '')
EOF
)
    [ -n "$wd_fails" ] || wd_fails=0
    if [ "$wd_status" = "locked" ] && [ "$fw_rules" -gt 0 ] && [ "$desired" != "off" ] && [ "$transitioning" != true ]; then
      state=LOCKED
    elif { [ "$wd_status" = "degraded" ]; } && [ "$svc_state" = "active" ] && [ "$desired" != "off" ] && [ "$transitioning" != true ]; then
      state=DEGRADED
    fi
    server_tag=$(python3 -c 'import json;print(json.load(open("/home/m26/AI/singbox/selected-server.json")).get("tag",""))' 2>/dev/null)
    lat=$(python3 - <<'EOF' 2>/dev/null
import json, socket, time
try:
    cfg = json.load(open('/home/m26/AI/singbox/config-full.json'))
    p = next((o for o in cfg.get('outbounds', []) if o.get('server')), None)
    if not p:
        raise SystemExit
    t0 = time.time()
    socket.create_connection((p['server'], p['server_port']), timeout=2).close()
    print(max(1, int((time.time() - t0) * 1000)))
except Exception:
    print('null')
EOF
)
    DESIRED="$desired" STATE="$state" SVC="$svc" SVC_STATE="$svc_state" FW="$fw_rules" TUN="$tun_up" EXIT_IP="$exit_ip" SERVER_TAG="$server_tag" LAT="$lat" WD_STATUS="$wd_status" WD_FAILS="$wd_fails" WD_NEXT="$wd_next" PROFILE="$PROFILE" python3 -c '
import json, os
lat = os.environ["LAT"]
print(json.dumps({
  "desired_mode": os.environ["DESIRED"],
  "profile": os.environ["PROFILE"],
  "actual_state": os.environ["STATE"],
  "service": os.environ["SVC"],
  "service_state": os.environ["SVC_STATE"],
  "firewall_rules": int(os.environ["FW"]),
  "tun0": os.environ["TUN"] == "true",
  "exit_ip": os.environ["EXIT_IP"] or None,
  "server_tag": os.environ["SERVER_TAG"] or None,
  "latency_ms": int(lat) if lat != "null" else None,
  "watchdog_status": os.environ.get("WD_STATUS") or None,
  "consecutive_failures": int(os.environ.get("WD_FAILS") or 0),
  "next_retry": os.environ.get("WD_NEXT") or None
}))
'
    ;;
  status)
    echo "mode: $(cat "$MODE_FILE" 2>/dev/null || echo unknown)"
    for s in sing-box.service sing-box-proxy.service sing-box-full.service; do
      echo "$s: $(systemctl --user is-active "$s" 2>/dev/null || echo inactive)"
    done
    echo "firewall rules: $(sudo -n firewall-cmd --direct --get-all-rules 2>/dev/null | wc -l)"
    if ip link show tun0 >/dev/null 2>&1; then echo "tun0: present"; else echo "tun0: absent"; fi
    EXIT=$(curl -s -m 5 https://api.ipify.org 2>/dev/null)
    if [ -n "$EXIT" ]; then echo "exit IP: $EXIT"; else echo "exit IP: unreachable"; fi
    ;;
  *) bash ~/AI/neodon-flatpak/firefox-proxy.sh restore || true; if systemctl --user is-active sing-box.service >/dev/null 2>&1; then systemctl --user stop sing-box.service && bash ~/AI/singbox/dns-fix.sh restore || true; set_mode off && echo "VPN OFF" && notify "VPN OFF"; else stop_all && fw_flush && systemctl --user start sing-box.service && bash ~/AI/singbox/dns-fix.sh apply || true; set_mode smart && echo "VPN SMART ON" && notify "VPN SMART ON"; fi;;
esac