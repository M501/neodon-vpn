#!/bin/bash
# neodon-heal — убрать весь сетевой след VPN, когда туннеля нет.
# Идемпотентно, безопасно в любой момент. Ничего не делает, пока хоть один
# sing-box жив (в т.ч. в состоянии activating/auto-restart).
#
# Зачем: unlock killswitch / resolv / ip-rule раньше жил ТОЛЬКО внутри
# app-тоггла. Умер сервис, приложение закрыто или .mode рассинхронился —
# чистить было некому, и интернет не возвращался до ребута.
set -u
SBOX="$HOME/AI/singbox"
mode=$(cat "$SBOX/.mode" 2>/dev/null || echo off)

running=0
for u in sing-box.service sing-box-full.service sing-box-proxy.service; do
  st=$(systemctl --user is-active "$u" 2>/dev/null)
  case "$st" in active|activating|reloading|auto-restart) running=1;; esac
  sub=$(systemctl --user show -p SubState --value "$u" 2>/dev/null)
  case "$sub" in auto-restart) running=1;; esac
done
if [ "$running" = 1 ]; then
  echo "heal: tunnel busy — nothing to do"
  exit 0
fi
# restart-in-flight guard: ExecStopPost fires between stop and start of an
# explicit `systemctl restart` — a fresh transition marker means the tunnel
# is coming back, not gone (otherwise .mode/resolv got wiped mid-server-switch).
if [ -f "$SBOX/.transitioning" ]; then
  _age=$(( $(date +%s) - $(stat -c %Y "$SBOX/.transitioning" 2>/dev/null || echo 0) ))
  if [ "$_age" -le 20 ]; then
    echo "heal: restart in flight (marker ${_age}s old) — skip"
    exit 0
  fi
fi

did=""
# 1) fail-closed killswitch (REJECT) — именно он гасит internet целиком
if sudo -n firewall-cmd --direct --get-all-rules 2>/dev/null | grep -q 'filter OUTPUT_direct 20 '; then
  bash "$SBOX/killswitch.sh" remove >/dev/null 2>&1 && did="$did firewall"
fi
# 2) policy-rules/таблица sing-box (остаются, если процесс убили без cleanup)
if ip rule show | grep -qE '^900[0-9]:|^9010:'; then
  for p in 9000 9001 9002 9003 9004 9005 9006 9007 9008 9009 9010; do
    sudo -n ip rule del pref "$p" 2>/dev/null
  done
  sudo -n ip route flush table 2022 2>/dev/null
  did="$did iprules"
fi
# 3) осиротевший tun0 — проглотит весь трафик
if ip link show tun0 >/dev/null 2>&1; then
  sudo -n ip link del tun0 2>/dev/null && did="$did tun0"
fi
# 4) подмена resolv.conf
if grep -q 'neodon-vpn static' /etc/resolv.conf 2>/dev/null; then
  bash "$SBOX/dns-fix.sh" restore >/dev/null 2>&1 && did="$did resolv"
fi
# 5) .mode не должен объявлять режим, которого нет
if [ "$mode" != "off" ]; then
  echo off > "$SBOX/.mode"; did="$did mode($mode-to-off)"
fi

if [ -n "$did" ]; then
  printf '%s HEAL: cleaned%s (was mode=%s)\n' "$(date +%s)" "$did" "$mode" >> "$HOME/AI/neodon-vpn/transitions.log"
  echo "heal: cleaned$did"
else
  echo "heal: clean"
fi
