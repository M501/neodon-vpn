#!/usr/bin/env bash
# QA pass C (host): REAL install into a fake HOME. Live system must be untouched.
# Usage: bash release/qa-sandbox.sh /tmp/neodon-vpn-<ver>.tar.gz
# Requires passwordless sudo (else sudo -v would prompt mid-test).
set -euo pipefail
T="${1:?tarball path required}"
sudo -n true 2>/dev/null || { echo "need passwordless sudo for sandbox QA" >&2; exit 2; }
FH=/tmp/neodon-fakehome
rm -rf "$FH" /tmp/neodon-qa-rel
mkdir -p "$FH"
# keep the real user site-packages visible under the fake HOME
REALSITE="$(python3 -c 'import site; print(site.getusersitepackages())' 2>/dev/null || true)"
export PYTHONPATH="${REALSITE}${PYTHONPATH:+:$PYTHONPATH}"
# block the real steam-shortcut registration during sandbox runs
mkdir -p "$FH/.local/share"
touch "$FH/.local/share/neodon-steam-shortcut.done"
mkdir -p /tmp/neodon-qa-rel
tar -xzf "$T" -C /tmp/neodon-qa-rel
R=/tmp/neodon-qa-rel/neodon-rel
LIVE_PY="$(md5sum ~/AI/neodon-vpn/neodon-vpn.py | cut -d' ' -f1)"
LIVE_MODE="$(cat ~/AI/singbox/.mode 2>/dev/null || echo none)"
echo "qa-sandbox: installing with HOME=$FH"
HOME="$FH" USER="${USER:-m26}" bash "$R/install.sh" --no-verify >/tmp/neodon-qa-sandbox.log 2>&1
echo "qa-sandbox: asserting layout"
fail=0
chk() { [ -e "$FH/$1" ] && echo "  ok: ~/$1" || { echo "  FAIL: ~/$1"; fail=1; }; }
chk "AI/singbox/singbox-toggle.sh"
chk "AI/singbox/singbox-server.sh"
chk "AI/singbox/killswitch.sh"
chk "AI/singbox/dns-fix.sh"
chk "AI/neodon-vpn/neodon-vpn.py"
chk ".local/bin/neodon-gui"
chk ".local/bin/neodon-hostctl"
chk ".local/share/applications/io.neodon.gui.desktop"
[ -n "$(ls "$FH"/AI/singbox/profiles/*.json 2>/dev/null)" ] && echo "  ok: profiles" || { echo "  FAIL: profiles"; fail=1; }
[ -x "$FH/.local/bin/neodon-gui" ] && echo "  ok: launcher executable" || { echo "  FAIL: launcher bit"; fail=1; }
QT_QPA_PLATFORM=offscreen python3 -c "import ast; ast.parse(open('$FH/AI/neodon-vpn/neodon-vpn.py').read()); print('  ok: gui parses')" || { echo "  FAIL: gui parse"; fail=1; }
echo "qa-sandbox: live system untouched?"
[ "$(md5sum ~/AI/neodon-vpn/neodon-vpn.py | cut -d' ' -f1)" = "$LIVE_PY" ] && echo "  ok: live gui intact" || { echo "  FAIL: live gui MODIFIED"; fail=1; }
[ "$(cat ~/AI/singbox/.mode 2>/dev/null || echo none)" = "$LIVE_MODE" ] && echo "  ok: live mode intact" || { echo "  FAIL: live mode MODIFIED"; fail=1; }
rm -rf "$FH" /tmp/neodon-qa-rel
[ "$fail" = 0 ] && echo "QA-SANDBOX OK" || { echo "QA-SANDBOX FAILED"; exit 1; }
