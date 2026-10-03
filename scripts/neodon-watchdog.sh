#!/bin/bash
# neodon-watchdog — интернет не должен умирать вместе с VPN.
#  (1) туннеля нет, а след остался (приложение закрыто / сервис упал /
#      .mode рассинхронился) -> heal: снимаем REJECT, resolv, ip-rule.
#  (2) TUNNEL-режим (fail-closed) с мёртвым data-path -> unlock + OFF
#      после 3 подряд неудачных exit-проб (не мгновенно, чтобы не дёргаться
#      на разовых выбросах под торрентом).
# Проверки дешёвые: пока режим не full, вся работа = 3 systemctl + чтение файлов.
set -u
SBOX="$HOME/AI/singbox"
FAILSTATE="$SBOX/.watchdog-fails"
mode=$(cat "$SBOX/.mode" 2>/dev/null || echo off)

running=0
for u in sing-box.service sing-box-full.service sing-box-proxy.service; do
  st=$(systemctl --user is-active "$u" 2>/dev/null)
  case "$st" in active|activating|reloading|auto-restart) running=1;; esac
done

if [ "$running" = 0 ]; then
  rm -f "$FAILSTATE"
  exec bash "$SBOX/neodon-heal.sh"
fi

# NM-guard (2026-10-02): probes are meaningless while the network is going
# down/up (sleep teardown, wifi reassociation). Never count those as dead.
nmstate=$(nmcli -t -f DEVICE,STATE device 2>/dev/null | awk -F: '$1=="wlan0"{print $2}')
if [ "$nmstate" != "connected" ]; then
  rm -f "$FAILSTATE"
  exit 0
fi

# живой туннель: следим только за TUN-режимами; блэкаут = нет exit-IP
# И одновременно нет прямого выхода (иначе это просто деградация сервера,
# при которой обычный интернет жив — выключать VPN тогда нельзя).
case "$mode" in full|smart) : ;; *) rm -f "$FAILSTATE"; exit 0 ;; esac
ip link show tun0 >/dev/null 2>&1 || exit 0

exit_ip=$(curl -s -m 6 https://api.ipify.org 2>/dev/null)
if [ -n "$exit_ip" ]; then rm -f "$FAILSTATE"; exit 0; fi
direct=$(curl -s -m 6 -o /dev/null -w '%{http_code}' https://ya.ru 2>/dev/null)
if [ -n "$direct" ] && [ "$direct" != "000" ]; then rm -f "$FAILSTATE"; exit 0; fi

fails=$(cat "$FAILSTATE" 2>/dev/null || echo 0)
fails=$((fails + 1)); echo "$fails" > "$FAILSTATE"
if [ "$fails" -lt 3 ]; then
  echo "watchdog: no internet ($fails/3) — exit-probe and direct-probe both dead"
  exit 0
fi
printf '%s WATCHDOG: internet dead %s probes -> unlock + OFF (internet first)\n' \
  "$(date +%s)" "$fails" >> "$HOME/AI/neodon-vpn/transitions.log"
bash "$SBOX/singbox-toggle.sh" off >/dev/null 2>&1
rm -f "$FAILSTATE"
echo "watchdog: internet dead -> OFF"
