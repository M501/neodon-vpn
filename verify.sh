#!/usr/bin/env bash
# Neodon VPN post-install verify. Exit code = number of failures (0 = VERIFY OK).
# Optional integrations (decky/steam) warn, never fail.
set -uo pipefail
FAIL=0
ok()   { echo "  ok: $*"; }
bad()  { echo "  FAIL: $*"; FAIL=$((FAIL + 1)); }
warn() { echo "  warn: $*"; }

echo "neodon-verify:"
python3 -m py_compile ~/AI/neodon-vpn/neodon-vpn.py 2>/dev/null \
  && ok "gui compiles" || bad "gui missing/broken"
~/AI/singbox/singbox-toggle.sh status-json 2>/dev/null | python3 -c "import json,sys; d=json.load(sys.stdin); assert 'actual_state' in d" 2>/dev/null \
  && ok "backend status-json" || bad "backend status broken"
[ -f ~/.local/share/applications/io.neodon.gui.desktop ] \
  && ok "desktop file" || bad "desktop file missing"
sudo -n test -f /etc/sudoers.d/neodon-vpn 2>/dev/null \
  && (sudo -n visudo -c >/dev/null 2>&1 && ok "sudoers valid" || bad "sudoers INVALID") \
  || warn "no sudoers file (manual sudo steps)"
ls ~/.config/systemd/user/sing-box*.service >/dev/null 2>&1 \
  && ok "sing-box units present" || bad "sing-box units missing"
[ -d ~/homebrew/plugins/neodon-vpn ] \
  && ok "decky plugin present" || warn "decky plugin absent (optional)"
command -v steamos-add-to-steam >/dev/null 2>&1 \
  && ok "steam tooling present" || warn "no steamos-add-to-steam (optional)"

if [ "$FAIL" = 0 ]; then echo "VERIFY OK"; else echo "VERIFY FAILED ($FAIL)"; fi
exit "$FAIL"
