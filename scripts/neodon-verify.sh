#!/usr/bin/env bash
# Phase 8: Neodon Verify — 8 тестов без пароля + E2E + killswitch proof
# Запуск: bash ~/AI/scripts/neodon-verify.sh
# Каждый тест — без echo пароль | sudo -S, только sudo -n внутри скриптов.
# Требует: Phase 6+7 выполнены, sing-box configs валидны, хост онлайн.
set -uo pipefail

AI="$HOME/AI"
SB_BIN="/usr/local/bin/sing-box"
HOST_PFX="79.139"
OUT="/tmp/neodon-verify.log"
SUM="/tmp/neodon-verify-summary.txt"
: > "$OUT"; : > "$SUM"
say() { echo "$1" | tee -a "$OUT"; echo "$1" >> "$SUM"; }
ok()  { say "PASS | $1"; }
bad() { say "FAIL | $1"; }
info(){ say "INFO | $1"; }

trap 'say "=== ABORT $(date -Iseconds) ==="; cat "$SUM"' ERR

# helpers
is_vpn() { case "$1" in $HOST_PFX*|TIMEOUT|""|-) return 1 ;; *) return 0 ;; esac; }
svc()  { systemctl --user is-active sing-box.service 2>/dev/null || echo dead; }
svcf() { systemctl --user is-active sing-box-full.service 2>/dev/null || echo dead; }
svcp() { systemctl --user is-active sing-box-proxy.service 2>/dev/null || echo dead; }
fw()   { sudo -n firewall-cmd --direct --get-all-rules 2>/dev/null | wc -l; }

say "=== NEODON VERIFY $(date '+%F %T') ==="
say "Хост: $(hostname)  IP: $(hostname -I 2>/dev/null | awk '{print $1}')  Uptime: $(uptime -p 2>/dev/null)"
say ""

# Pre: passwordless gate — если не проходит, дальше нет смысла
info "PRE: passwordless gate"
if sudo -n firewall-cmd --direct --get-all-rules >/dev/null 2>&1; then ok "PRE sudo -n firewall-cmd --direct без пароля (rules=$(fw))"; else bad "PRE sudo -n firewall-cmd --direct FAIL — проверь /etc/sudoers.d/90-singbox-killswitch"; fi
if getcap "$SB_BIN" 2>/dev/null | grep -q cap_net_admin; then ok "PRE cap_net_admin на sing-box"; else bad "PRE нет cap_net_admin (getcap: $(getcap "$SB_BIN" 2>&1))"; fi
for c in config.json config-full.json config-proxy.json; do
  if [ -f "$AI/singbox/$c" ] && "$SB_BIN" check -c "$AI/singbox/$c" >/dev/null 2>&1; then ok "PRE $c check"; else bad "PRE $c check FAIL ($AI/singbox/$c)"; fi
done
say ""

# T1: OFF status без пароля
info "T1: OFF status (без пароля)"
"$AI/neodon-hostctl" stop >/dev/null 2>&1 || bash "$AI/singbox/singbox-toggle.sh" off >/dev/null 2>&1 || true
sleep 3
st=$("$AI/neodon-hostctl" status 2>/dev/null | python3 -c 'import json,sys; d=json.load(sys.stdin); print(d.get("actual_state","?"))' 2>/dev/null || echo "?")
fwc=$(fw); tun=$(ip link show tun0 >/dev/null 2>&1 && echo present || echo absent)
if [ "$st" = "OFF" ] && [ "$fwc" -eq 0 ] && [ "$tun" = "absent" ]; then ok "T1 OFF state=$st fw=$fwc tun=$tun"; else bad "T1 OFF state=$st fw=$fwc tun=$tun (ожидали OFF 0 absent)"; fi

# T2: PROXY ON без пароля
info "T2: PROXY ON (без пароля)"
"$AI/neodon-hostctl" start proxy >/dev/null 2>&1; sleep 5
st=$("$AI/neodon-hostctl" status 2>/dev/null | python3 -c 'import json,sys; d=json.load(sys.stdin); print(d.get("actual_state","?"))' 2>/dev/null || echo "?")
lsn=$(ss -tlnp 2>/dev/null | grep -q 10808 && echo LISTEN || echo no)
if [ "$st" = "CONNECTED" ] || [ "$st" = "STARTING" ]; then
  if [ "$lsn" = "LISTEN" ]; then ok "T2 PROXY state=$st 10808=$lsn"; else bad "T2 PROXY state=$st но 10808 не слушает"; fi
  # E2E: curl via proxy → VPN IP, direct → ISP
  vpn_ip=$(curl -s -m 6 -x socks5h://127.0.0.1:10808 https://api.ipify.org 2>/dev/null || echo TIMEOUT)
  isp_ip=$(curl -s -m 6 https://api.ipify.org 2>/dev/null || echo TIMEOUT)
  if is_vpn "$vpn_ip"; then ok "T2 PROXY curl via socks5 → $vpn_ip (VPN)"; else bad "T2 PROXY curl via socks5 → $vpn_ip (ожидали VPN)"; fi
  # isp может быть VPN если уже в туннеле — не фейлим, только info
  info "T2 direct IP: $isp_ip (ожидается ISP $HOST_PFX.* если не в TUNNEL)"
else
  bad "T2 PROXY state=$st (ожидали CONNECTED/STARTING) — journal: $(journalctl --user -u sing-box-proxy.service -n 20 --no-pager 2>&1 | grep -iE 'error|fail' | tail -1 | head -c 200)"
fi

# T3: server switch в PROXY без пароля
info "T3: server switch в PROXY (без пароля)"
if [ -f "$AI/neodon-sub/raw.json" ]; then
  before=$("$AI/neodon-hostctl" status 2>/dev/null | python3 -c 'import json,sys; print(json.load(sys.stdin).get("server_tag",""))' 2>/dev/null || echo "")
  # взять другой сервер (если 0, то 1, иначе 0)
  target=1; [ "$before" = "" ] && target=0
  out=$(bash "$AI/singbox/singbox-server.sh" set "$target" 2>&1 | tail -3 | head -c 300) || true
  sleep 4
  after=$("$AI/neodon-hostctl" status 2>/dev/null | python3 -c 'import json,sys; print(json.load(sys.stdin).get("server_tag",""))' 2>/dev/null || echo "")
  if [ -n "$after" ]; then ok "T3 server switch → $after (было: $before) | $out"; else bad "T3 server switch FAIL | $out"; fi
else
  info "T3 SKIP — нет raw.json (подписка не fetched)"
fi

# T4: TUNNEL ON без пароля
info "T4: TUNNEL ON (без пароля)"
"$AI/neodon-hostctl" start full >/dev/null 2>&1; sleep 9
st=$("$AI/neodon-hostctl" status 2>/dev/null | python3 -c 'import json,sys; d=json.load(sys.stdin); print(d.get("actual_state","?"))' 2>/dev/null || echo "?")
tun=$(ip link show tun0 >/dev/null 2>&1 && echo present || echo absent)
fwc=$(fw)
vpn_ip=$(curl -s -m 6 https://api.ipify.org 2>/dev/null || echo TIMEOUT)
if [ "$tun" = "present" ] && [ "$fwc" -ge 10 ] && is_vpn "$vpn_ip"; then
  ok "T4 TUNNEL tun=$tun fw=$fwc ip=$vpn_ip state=$st"
  if sudo -n firewall-cmd --direct --get-all-rules 2>/dev/null | grep -q "REJECT"; then ok "T4 killswitch REJECT present"; else bad "T4 killswitch REJECT missing"; fi
else
  bad "T4 TUNNEL tun=$tun fw=$fwc ip=$vpn_ip state=$st (ожидали present ≥10 VPN)"
fi

# T5: server switch в TUNNEL (killswitch reinstall) без пароля
info "T5: server switch в TUNNEL (без пароля, killswitch reinstall)"
if [ -f "$AI/neodon-sub/raw.json" ] && [ "$(svcf)" = "active" ]; then
  out=$(bash "$AI/singbox/singbox-server.sh" set 2 2>&1 | tail -3 | head -c 300) || true
  sleep 4
  fwc2=$(fw); tun2=$(ip link show tun0 >/dev/null 2>&1 && echo present || echo absent)
  if [ "$tun2" = "present" ] && [ "$fwc2" -ge 10 ]; then ok "T5 TUNNEL server switch OK tun=$tun2 fw=$fwc2 | $out"; else bad "T5 TUNNEL server switch tun=$tun2 fw=$fwc2 | $out"; fi
else
  info "T5 SKIP — не в TUNNEL или нет raw.json"
fi

# T6: OFF без пароля (снятие туннеля + firewall)
info "T6: OFF (без пароля, снятие TUNNEL)"
"$AI/neodon-hostctl" stop >/dev/null 2>&1; sleep 4
st=$("$AI/neodon-hostctl" status 2>/dev/null | python3 -c 'import json,sys; d=json.load(sys.stdin); print(d.get("actual_state","?"))' 2>/dev/null || echo "?")
fwc=$(fw); tun=$(ip link show tun0 >/dev/null 2>&1 && echo present || echo absent)
isp_ip=$(curl -s -m 6 https://api.ipify.org 2>/dev/null || echo TIMEOUT)
if [ "$st" = "OFF" ] && [ "$fwc" -eq 0 ] && [ "$tun" = "absent" ]; then
  ok "T6 OFF state=$st fw=$fwc tun=$tun ip=$isp_ip"
  if echo "$isp_ip" | grep -q "$HOST_PFX"; then ok "T6 ISP IP $isp_ip (домашний)"; else info "T6 IP $isp_ip (не $HOST_PFX — проверь, может VPN ещё)"; fi
else
  bad "T6 OFF state=$st fw=$fwc tun=$tun ip=$isp_ip (ожидали OFF 0 absent)"
fi

# T7: profile switch + Full invariant
info "T7: profile switch + TUNNEL invariant (без пароля)"
if [ -f "$AI/singbox/apply-profile.py" ]; then
  # Full invariant: md5 config-full.json до/после apply-profile не меняется
  if [ -f "$AI/singbox/config-full.json" ]; then
    md5_before=$(md5sum "$AI/singbox/config-full.json" 2>/dev/null | cut -d' ' -f1)
  else
    md5_before="none"
  fi
  # пробуем popular-ai (или default если нет)
  for pid in popular-ai basic-set default; do
    if python3 "$AI/singbox/apply-profile.py" --check "$pid" >/dev/null 2>&1; then
      target="$pid"; break
    fi
  done
  if [ -n "${target:-}" ]; then
    if python3 "$AI/singbox/apply-profile.py" "$target" 2>&1 | tail -5 | head -c 500; then
      ok "T7 profile $target apply OK"
    else
      bad "T7 profile $target apply FAIL"
    fi
    if [ "$md5_before" != "none" ] && [ -f "$AI/singbox/config-full.json" ]; then
      md5_after=$(md5sum "$AI/singbox/config-full.json" 2>/dev/null | cut -d' ' -f1)
      if [ "$md5_before" = "$md5_after" ]; then ok "T7 TUNNEL invariant: config-full.json unchanged ($md5_before)"; else bad "T7 TUNNEL invariant FAIL: $md5_before → $md5_after (Full должен игнорировать профиль)"; fi
    fi
    # вернуть default
    python3 "$AI/singbox/apply-profile.py" default >/dev/null 2>&1 || true
  else
    info "T7 SKIP — нет валидных профилей для --check"
  fi
else
  info "T7 SKIP — нет apply-profile.py"
fi

# T8: Killswitch proof (fail-closed) — только если можем войти в TUNNEL
info "T8: Killswitch proof (fail-closed, без пароля)"
"$AI/neodon-hostctl" start full >/dev/null 2>&1; sleep 8
if [ "$(svcf)" = "active" ] && ip link show tun0 >/dev/null 2>&1; then
  systemctl --user stop sing-box-full.service 2>&1 | head -3 || true
  sleep 3
  fwc=$(fw)
  # при dead-сервисе firewall должен остаться LOCKED (fail-closed) — интернет заблокирован
  code_wan=$(curl -4 -s -o /dev/null -m 5 -w '%{http_code}' http://9.9.9.9 2>/dev/null || true); [ -z "$code_wan" ] && code_wan=000; code_wan=$(echo "$code_wan" | tr -d '\n\r ' | head -c 3)
  code_lan=$(curl -4 -s -o /dev/null -m 3 -w '%{http_code}' http://192.168.3.1 2>/dev/null || true); [ -z "$code_lan" ] && code_lan=000; code_lan=$(echo "$code_lan" | tr -d '\n\r ' | head -c 3)
  if [ "$code_wan" = "000" ]; then ok "T8 killswitch: WAN blocked (code=$code_wan) fw=$fwc — fail-closed OK"; else bad "T8 killswitch: WAN NOT blocked (code=$code_wan) — УТЕЧКА!"; fi
  if [ "$code_lan" != "000" ]; then ok "T8 LAN accessible (code=$code_lan)"; else bad "T8 LAN NOT accessible (code=$code_lan)"; fi
  # восстановить
  systemctl --user start sing-box-full.service 2>&1 | head -3 || true
  sleep 6
  vpn_ip=$(curl -s -m 6 https://api.ipify.org 2>/dev/null || echo TIMEOUT)
  if is_vpn "$vpn_ip"; then ok "T8 после restart VPN восстановлен ip=$vpn_ip"; else bad "T8 после restart не восстановлен ip=$vpn_ip"; fi
  "$AI/neodon-hostctl" stop >/dev/null 2>&1; sleep 3
else
  info "T8 SKIP — не удалось войти в TUNNEL (service $(svcf), tun $(ip link show tun0 2>&1 | head -1 | head -c 80))"
  "$AI/neodon-hostctl" stop >/dev/null 2>&1 || true
fi

# E2E: PROXY routing proof (journalctl outbound)
info "E2E: PROXY routing (требует PROXY ON)"
"$AI/neodon-hostctl" start proxy >/dev/null 2>&1; sleep 5
# запустить curl через proxy и без, проверить outbound в журнале
curl -x socks5h://127.0.0.1:10808 -s -o /dev/null -m 6 https://youtube.com 2>/dev/null || true
sleep 1
curl -x socks5h://127.0.0.1:10808 -s -o /dev/null -m 6 https://ozon.ru 2>/dev/null || true
sleep 1
log=$(journalctl --user -u sing-box-proxy.service -u sing-box.service --since '30 seconds ago' --no-pager 2>&1 | grep -iE 'youtube|ozon|outbound' | tail -20 || echo "no log")
if echo "$log" | grep -qi "youtube.*proxy\|proxy.*youtube\|vless"; then ok "E2E youtube → proxy (log: $(echo "$log" | grep -i youtube | tail -1 | head -c 150))"; else info "E2E youtube log: $(echo "$log" | tail -5 | head -c 500)"; fi
if echo "$log" | grep -qi "ozon.*direct\|direct.*ozon"; then ok "E2E ozon → direct"; else info "E2E ozon log: $(echo "$log" | grep -i ozon | tail -1 | head -c 200)"; fi
"$AI/neodon-hostctl" stop >/dev/null 2>&1; sleep 2

say ""
say "=== SUMMARY ==="
cat "$SUM" 2>&1 | grep -E "^(PASS|FAIL)" | sort | uniq -c | head -20 || true
pass=$(grep -c "^PASS" "$SUM" 2>/dev/null || true); pass=$(echo "$pass" | head -n1 | tr -d ' \n\r'); [ -z "$pass" ] && pass=0
fail=$(grep -c "^FAIL" "$SUM" 2>/dev/null || true); fail=$(echo "$fail" | head -n1 | tr -d ' \n\r'); [ -z "$fail" ] && fail=0
say "Итого: PASS=$pass FAIL=$fail"
if [ "$fail" -eq 0 ]; then say "=== VERIFY OK ==="; else say "=== VERIFY FAIL ($fail) ==="; fi
say "Лог: $OUT"
say "Саммари: $SUM"
[ "$fail" -eq 0 ] || exit 1
