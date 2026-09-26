#!/bin/bash
# Neodon tunnel guard: full-режим льёт ВЕСЬ трафик через VPN (квота подписки).
# Не даём ему висеть без присмотра: авто-демоут full->smart после лимита.
# Лимит: NEODON_FULL_LIMIT секунд (по умолчанию 1800 = 30 мин).
export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"
cd "$HOME/AI/singbox" || exit 0
mode=$(cat .mode 2>/dev/null || echo unknown)
if [ "$mode" != "full" ]; then rm -f .full-since; exit 0; fi
now=$(date +%s)
since=$(cat .full-since 2>/dev/null || echo "")
if [ -z "$since" ]; then echo "$now" > .full-since; exit 0; fi
age=$(( now - since ))
limit=${NEODON_FULL_LIMIT:-1800}
[ "$age" -ge "$limit" ] || exit 0
bash "$HOME/AI/singbox/singbox-toggle.sh" smart >/dev/null 2>&1
rm -f .full-since
printf '%s TUNNEL-GUARD: full->smart after %ss (quota protection)\n' "$now" "$age" >> "$HOME/AI/neodon-vpn/transitions.log"
