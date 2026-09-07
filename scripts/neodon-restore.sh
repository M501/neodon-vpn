#!/usr/bin/env bash
# Phase 6: Neodon SD → Host Restore
# Копирует SD /run/media/m26/0000-D182/neodon-vpn → ~/AI, ставит sing-box 1.13.18 + caps,
# готовит директории. Запуск на базе (m26@bazzite):  bash ~/AI/scripts/neodon-restore.sh
# Требуется один раз sudo пароль для /usr/local/bin + setcap + sudoers (дальше всё без пароля).
set -euo pipefail

SD="/run/media/m26/0000-D182/neodon-vpn"
AI="$HOME/AI"
SB_BIN="/usr/local/bin/sing-box"
LOG="/tmp/neodon-restore.log"
exec > >(tee -a "$LOG") 2>&1

say() { echo "[$(date +%H:%M:%S)] $*"; }
die() { echo "ERROR: $*" >&2; exit 1; }
need_sd() { [ -d "$SD" ] || die "SD не найдена: $SD (вставь карту, проверь /run/media/m26/)"; }

say "=== Phase 6: Neodon SD → Host Restore ==="
need_sd
ls -lh "$SD/sing-box" 2>/dev/null | head -1 || die "sing-box не найден на SD"
say "SD OK: $(ls "$SD" | tr '\n' ' ')"

# 1. Директории
say "--- 1. Директории ~/AI ---"
mkdir -p "$AI/neodon-vpn" "$AI/singbox" "$AI/singbox/profiles" "$AI/neodon-sub" "$AI/neodon-flatpak" "$AI/scripts" ~/.config/systemd/user
say "dirs OK"

# 2. Копирование SD → Host (бережно, не затираем .mode/.profile если есть)
say "--- 2. Копирование SD → Host ---"
cp -a "$SD/neodon-vpn.py" "$AI/neodon-vpn/neodon-vpn.py"
cp -a "$SD/neodon-hostctl" "$AI/neodon-hostctl"
cp -a "$SD/singbox-toggle.sh" "$AI/singbox/singbox-toggle.sh"
cp -a "$SD/singbox-server.sh" "$AI/singbox/singbox-server.sh"
cp -a "$SD/killswitch.sh" "$AI/singbox/killswitch.sh"
cp -a "$SD/neodon-sub.py" "$AI/neodon-sub/neodon-sub.py"
cp -a "$SD/io.neodon.gui.json" "$AI/neodon-vpn/io.neodon.gui.json" 2>/dev/null || true
cp -a "$SD/README.md" "$AI/neodon-vpn/README.md" 2>/dev/null || true
cp -a "$SD/.gitignore" "$AI/neodon-vpn/.gitignore" 2>/dev/null || true
if [ -d "$SD/flags" ]; then cp -a "$SD/flags" "$AI/neodon-vpn/flags" 2>/dev/null || true; fi
if [ -d "$SD/app" ]; then cp -a "$SD/app"/* "$AI/neodon-vpn/" 2>/dev/null || true; fi
# firefox-proxy.sh нет на SD — берём из этого репо если есть, иначе создаём
if [ -f "$AI/scripts/firefox-proxy.sh" ]; then
  cp -a "$AI/scripts/firefox-proxy.sh" "$AI/neodon-flatpak/firefox-proxy.sh"
elif [ ! -f "$AI/neodon-flatpak/firefox-proxy.sh" ]; then
  cat > "$AI/neodon-flatpak/firefox-proxy.sh" <<'FPEOF'
#!/bin/bash
FF_PROFILE_ROOT="${FF_PROFILE_ROOT:-}"
if [ -z "$FF_PROFILE_ROOT" ]; then
  for d in "$HOME/.var/app/org.mozilla.firefox/.mozilla/firefox" "$HOME/.mozilla/firefox"; do [ -d "$d" ] && FF_PROFILE_ROOT="$d" && break; done
fi
[ -n "$FF_PROFILE_ROOT" ] || { echo "WARN: no Firefox profile dir"; exit 0; }
apply() { for prefs in "$FF_PROFILE_ROOT"/*/prefs.js; do [ -f "$prefs" ] || continue; rm -f "$prefs.neodon.bak"; cp "$prefs" "$prefs.neodon.bak"; sed -i '/user_pref("network\.proxy\.\(type\|socks\|socks_port\|socks_remote_dns\|share_proxy_settings\)"/d' "$prefs"; cat >> "$prefs" <<'EOF'
user_pref("network.proxy.type", 1);
user_pref("network.proxy.socks", "127.0.0.1");
user_pref("network.proxy.socks_port", 10808);
user_pref("network.proxy.socks_remote_dns", true);
user_pref("network.proxy.share_proxy_settings", true);
EOF
  done; }
restore() { for prefs in "$FF_PROFILE_ROOT"/*/prefs.js; do [ -f "$prefs" ] || continue; if [ -f "$prefs.neodon.bak" ]; then cp "$prefs.neodon.bak" "$prefs"; rm -f "$prefs.neodon.bak"; else sed -i '/user_pref("network\.proxy\.\(type\|socks\|socks_port\|socks_remote_dns\|share_proxy_settings\)"/d' "$prefs"; fi; done; }
case "${1:-}" in apply) apply;; restore) restore;; *) echo "usage: $0 apply|restore"; exit 1;; esac
FPEOF
fi
chmod +x "$AI/neodon-hostctl" "$AI/singbox/"*.sh "$AI/neodon-sub/"*.py "$AI/neodon-flatpak/firefox-proxy.sh" 2>/dev/null || true
say "copy OK"

# 3. sing-box binary + caps (требует sudo один раз)
say "--- 3. sing-box binary + caps ---"
if [ ! -f "$SB_BIN" ] || ! cmp -s "$SD/sing-box" "$SB_BIN" 2>/dev/null; then
  say "копирую sing-box в $SB_BIN (потребует sudo пароль один раз)..."
  sudo cp "$SD/sing-box" "$SB_BIN"
  sudo chmod +x "$SB_BIN"
else
  say "sing-box уже на месте, пропускаю cp"
fi
if command -v setcap >/dev/null 2>&1; then
  if ! getcap "$SB_BIN" 2>/dev/null | grep -q cap_net_admin; then
    say "ставлю caps cap_net_admin,cap_net_raw+ep..."
    sudo setcap cap_net_admin,cap_net_raw+ep "$SB_BIN" || echo "WARN: setcap failed (продолжаем, TUN потребует sudo)"
  fi
  getcap "$SB_BIN" 2>&1 | head -1 || true
else
  echo "WARN: setcap не найден"
fi
"$SB_BIN" version 2>&1 | head -1 || echo "WARN: sing-box version failed"
say "binary OK"

# 4. Проверка
say "--- 4. Проверка Phase 6 ---"
ls -lh "$SB_BIN" 2>&1 | head -1
getcap "$SB_BIN" 2>&1 | head -1 || true
ls -lh "$AI/neodon-hostctl" "$AI/singbox/"*.sh 2>&1 | head -20
echo "--- ~/AI tree ---"
find "$AI" -maxdepth 3 -type f -o -type l | head -40
say "=== Phase 6 DONE ==="
say "Лог: $LOG"
say "Дальше: bash $AI/scripts/neodon-config-gen.sh  (Phase 6-02)  или  bash $AI/scripts/neodon-passwordless.sh  (Phase 7)"
