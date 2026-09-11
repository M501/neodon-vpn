#!/usr/bin/env bash
# QA pass A (static, anywhere): tarball completeness + syntax + secrets.
# Usage: bash release/qa-static.sh /tmp/neodon-vpn-<ver>.tar.gz
set -euo pipefail
T="${1:?tarball path required}"
D=/tmp/neodon-qa-static
rm -rf "$D"; mkdir -p "$D"
tar -xzf "$T" -C "$D"
R="$D/neodon-rel"
fail=0
need() { [ -e "$R/$1" ] && echo "  ok: $1" || { echo "  FAIL: missing $1"; fail=1; }; }
echo "qa-static: manifest"
for f in install.sh verify.sh \
  bin/singbox-toggle.sh bin/singbox-server.sh bin/killswitch.sh bin/dns-fix.sh \
  bin/apply-profile.py bin/neodon-hostctl bin/neodon-vpn.py \
  systemd/sing-box.service systemd/sing-box-full.service systemd/sing-box-proxy.service \
  desktop/io.neodon.gui.desktop sudoers.d/neodon-vpn.template \
  decky/neodon-vpn/plugin.json decky/neodon-vpn/main.py decky/neodon-vpn/dist/index.js; do
  need "$f"
done
[ -n "$(ls "$R"/profiles/*.json 2>/dev/null)" ] && echo "  ok: profiles/*.json" || { echo "  FAIL: profiles empty"; fail=1; }
[ -n "$(ls "$R"/examples/*.example 2>/dev/null)" ] && echo "  ok: examples/*.example" || { echo "  FAIL: examples empty"; fail=1; }
[ -n "$(ls "$R"/flags/*.png 2>/dev/null)" ] && echo "  ok: flags/*.png" || { echo "  FAIL: flags empty"; fail=1; }
echo "qa-static: syntax"
for s in "$R"/install.sh "$R"/verify.sh "$R"/bin/*.sh; do
  bash -n "$s" && echo "  ok: bash -n $(basename "$s")" || { echo "  FAIL: syntax $s"; fail=1; }
done
if command -v cygpath >/dev/null 2>&1; then
  PY1="$(cygpath -w "$R/bin/neodon-vpn.py")"; PY2="$(cygpath -w "$R/decky/neodon-vpn/main.py")"
else
  PY1="$R/bin/neodon-vpn.py"; PY2="$R/decky/neodon-vpn/main.py"
fi
python3 -m py_compile "$PY1" "$PY2" \
  && echo "  ok: python compile" || { echo "  FAIL: python compile"; fail=1; }
echo "qa-static: secrets"
if grep -rEio '[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}' "$R" \
   | grep -v '00000000-0000-0000-0000-000000000000' | grep -q .; then
  echo "  FAIL: secret leak"; fail=1
else
  echo "  ok: no secrets"
fi
[ "$fail" = 0 ] && echo "QA-STATIC OK" || { echo "QA-STATIC FAILED"; exit 1; }
