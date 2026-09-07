#!/usr/bin/env bash
# Phase 7: Neodon Passwordless + systemd + PROXY/TUNNEL setup
# Делает всё без пароля после Phase 6 кроме первого sudo (sudoers/polkit).
# Запуск: bash ~/AI/scripts/neodon-passwordless.sh
set -euo pipefail

AI="$HOME/AI"
SB_BIN="/usr/local/bin/sing-box"
LOG="/tmp/neodon-passwordless.log"
exec > >(tee -a "$LOG") 2>&1
say() { echo "[$(date +%H:%M:%S)] $*"; }

say "=== Phase 7: Passwordless + systemd + PROXY/TUNNEL ==="

# 1. Passwordless: sudoers + polkit + caps
say "--- 1. Passwordless ---"
SUDOERS="/etc/sudoers.d/90-singbox-killswitch"
if [ ! -f "$SUDOERS" ] || ! grep -q "firewall-cmd --direct" "$SUDOERS" 2>/dev/null; then
  say "создаю $SUDOERS (потребует sudo)..."
  echo 'm26 ALL=(ALL) NOPASSWD: /usr/bin/firewall-cmd --direct *' | sudo tee "$SUDOERS" >/dev/null
  sudo chmod 440 "$SUDOERS"
  sudo visudo -c 2>&1 | head -5 || echo "WARN: visudo -c failed"
else
  say "sudoers уже есть"
fi
POLKIT="/etc/polkit-1/rules.d/50-singbox-resolve.rules"
if [ ! -f "$POLKIT" ]; then
  say "создаю $POLKIT..."
  sudo tee "$POLKIT" >/dev/null <<'RULE'
polkit.addRule(function(a,s){ if(a.id.indexOf("org.fedoraproject.FirewallD1.")==0 && s.user=="m26") return polkit.Result.YES; });
RULE
  sudo chmod 644 "$POLKIT"
else
  say "polkit rule уже есть"
fi
if command -v setcap >/dev/null 2>&1; then
  getcap "$SB_BIN" 2>/dev/null | grep -q cap_net_admin || { sudo setcap cap_net_admin,cap_net_raw+ep "$SB_BIN" 2>&1 | head -3; getcap "$SB_BIN" 2>&1 | head -1; }
fi
say "проверка passwordless:"
if sudo -n true 2>&1; then echo "  sudo -n true: OK"; else echo "  sudo -n true: FAIL (нужен пароль — проверь sudoers)"; fi
if sudo -n firewall-cmd --direct --get-all-rules >/dev/null 2>&1; then echo "  sudo -n firewall-cmd --direct: OK ($(sudo -n firewall-cmd --direct --get-all-rules 2>&1 | wc -l) rules)"; else echo "  sudo -n firewall-cmd --direct: FAIL"; fi
getcap "$SB_BIN" 2>&1 | head -1 || true

# 2. systemd --user units
say "--- 2. systemd --user units ---"
mkdir -p ~/.config/systemd/user
cat > ~/.config/systemd/user/sing-box.service <<'UNIT'
[Unit]
Description=Neodon VPN (smart/proxy)
After=network-online.target
Wants=network-online.target
[Service]
Type=simple
ExecStart=/usr/local/bin/sing-box run -c %h/AI/singbox/config.json
Restart=on-failure
RestartSec=3
[Install]
WantedBy=default.target
UNIT
cat > ~/.config/systemd/user/sing-box-full.service <<'UNIT'
[Unit]
Description=Neodon VPN (full/tunnel)
After=network-online.target
Wants=network-online.target
[Service]
Type=simple
ExecStart=/usr/local/bin/sing-box run -c %h/AI/singbox/config-full.json
Restart=on-failure
RestartSec=3
[Install]
WantedBy=default.target
UNIT
cat > ~/.config/systemd/user/sing-box-proxy.service <<'UNIT'
[Unit]
Description=Neodon VPN (proxy only)
After=network-online.target
Wants=network-online.target
[Service]
Type=simple
ExecStart=/usr/local/bin/sing-box run -c %h/AI/singbox/config-proxy.json
Restart=on-failure
RestartSec=3
[Install]
WantedBy=default.target
UNIT
cat > ~/.config/systemd/user/neodon-boot.service <<'UNIT'
[Unit]
Description=Neodon VPN autostart
After=network-online.target sing-box.service
[Service]
Type=oneshot
ExecStart=%h/AI/singbox/singbox-toggle.sh smart
RemainAfterExit=yes
[Install]
WantedBy=default.target
UNIT
say "юниты записаны"
systemctl --user daemon-reload 2>&1 | head -5 || true
systemctl --user enable neodon-boot.service sing-box.service sing-box-full.service sing-box-proxy.service 2>&1 | head -10 || true
say "daemon-reload + enable OK"
systemctl --user is-enabled sing-box.service sing-box-full.service sing-box-proxy.service neodon-boot.service 2>&1 | head -10 || true

# 3. sing-box check (если конфиги уже есть)
say "--- 3. sing-box check ---"
for c in config.json config-full.json config-proxy.json; do
  p="$AI/singbox/$c"
  if [ -f "$p" ]; then
    if "$SB_BIN" check -c "$p" 2>&1 | head -5; then echo "  $c: check PASS"; else echo "  $c: check FAIL"; fi
  else
    echo "  $c: не найден (нужен neodon-config-gen.sh)"
  fi
done

# 4. Итог
say "=== Phase 7 DONE ==="
say "Лог: $LOG"
say "Проверки без пароля:"
say "  sudo -n firewall-cmd --direct --get-all-rules | wc -l   # должно быть без пароля"
say "  ~/AI/neodon-hostctl status | python3 -m json.tool"
say "  bash ~/AI/singbox/singbox-toggle.sh status-json | python3 -m json.tool"
