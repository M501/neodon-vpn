#!/usr/bin/env bash
# Assemble neodon-vpn-<ver>.tar.gz from THIS REPO (reproducible, no secrets).
# Usage: bash release/stage.sh [ver]  (default 0.1.0)
# Output: /tmp/neodon-vpn-<ver>.tar.gz + .sha256
set -euo pipefail
VER="${1:-0.1.0}"
SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STAGE=/tmp/neodon-rel
rm -rf "$STAGE"
mkdir -p "$STAGE/bin" "$STAGE/systemd" "$STAGE/desktop" "$STAGE/sudoers.d" \
         "$STAGE/profiles" "$STAGE/icons" "$STAGE/flags" "$STAGE/examples" \
         "$STAGE/decky"
# backend scripts + hostctl + GUI
for f in singbox-toggle.sh singbox-server.sh killswitch.sh dns-fix.sh apply-profile.py neodon-hostctl; do
  [ -f "$SRC/scripts/$f" ] || { echo "repo broken: scripts/$f missing" >&2; exit 3; }
  cp "$SRC/scripts/$f" "$STAGE/bin/"
done
cp "$SRC/tests/app/neodon-vpn.py" "$STAGE/bin/neodon-vpn.py"
# units / desktop / sudoers / data
cp "$SRC"/systemd/*.service "$STAGE/systemd/"
cp "$SRC/desktop/io.neodon.gui.desktop" "$STAGE/desktop/"
[ -f "$SRC/desktop/io.neodon.gui.svg" ] && cp "$SRC/desktop/io.neodon.gui.svg" "$STAGE/desktop/"
cp "$SRC/sudoers.d/neodon-vpn.template" "$STAGE/sudoers.d/"
cp "$SRC"/profiles/*.json "$STAGE/profiles/"
[ -d "$SRC/icons" ] && cp -r "$SRC/icons/." "$STAGE/icons/" 2>/dev/null || true
cp "$SRC"/flags/*.png "$STAGE/flags/"
cp "$SRC"/examples/*.example "$STAGE/examples/"
# decky plugin (prebuilt dist/ committed in repo)
[ -f "$SRC/decky/neodon-vpn/dist/index.js" ] || { echo "repo broken: decky dist not built" >&2; exit 3; }
cp -r "$SRC/decky/neodon-vpn" "$STAGE/decky/"
rm -rf "$STAGE/decky/neodon-vpn/node_modules" "$STAGE/decky/neodon-vpn/dist/*.map"
# top-level entry points
cp "$SRC/install.sh" "$SRC/verify.sh" "$STAGE/"
cp "$SRC/README.md" "$STAGE/" 2>/dev/null || echo "# Neodon VPN $VER" > "$STAGE/README.md"
# secret scan: no UUIDs/keys outside the placeholder
if grep -rEio '[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}' "$STAGE" \
   | grep -v '00000000-0000-0000-0000-000000000000' | head -n 3 | grep -q .; then
  echo "SECRET LEAK in stage!" >&2; exit 4
fi
cd /tmp
rm -f "neodon-vpn-$VER.tar.gz" "neodon-vpn-$VER.tar.gz.sha256"
tar -czf "neodon-vpn-$VER.tar.gz" neodon-rel
sha256sum "neodon-vpn-$VER.tar.gz" > "neodon-vpn-$VER.tar.gz.sha256"
tar -tzf "neodon-vpn-$VER.tar.gz" | head -n 12
cat "neodon-vpn-$VER.tar.gz.sha256"
