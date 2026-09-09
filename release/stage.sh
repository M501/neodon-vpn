#!/usr/bin/env bash
# Assemble neodon-vpn-<ver>.tar.gz from the LIVE system (rc1 path).
# Repo-only files (install.sh, verify.sh, sudoers template) must be put to
# /tmp first: install.sh verify.sh sudoers-template.
set -euo pipefail
VER="${1:-0.1.0-rc1}"
STAGE=/tmp/neodon-rel
rm -rf "$STAGE"
mkdir -p "$STAGE/bin" "$STAGE/systemd" "$STAGE/desktop" "$STAGE/sudoers.d" \
         "$STAGE/profiles" "$STAGE/icons" "$STAGE/flags" "$STAGE/examples"
cp ~/AI/singbox/singbox-toggle.sh ~/AI/singbox/singbox-server.sh \
   ~/AI/singbox/killswitch.sh ~/AI/singbox/dns-fix.sh \
   ~/AI/singbox/apply-profile.py "$STAGE/bin/"
cp ~/AI/neodon-hostctl "$STAGE/bin/neodon-hostctl"
cp ~/AI/neodon-vpn/neodon-vpn.py "$STAGE/bin/"
cp ~/.config/systemd/user/sing-box*.service "$STAGE/systemd/"
cp ~/.local/share/applications/io.neodon.gui.desktop "$STAGE/desktop/" 2>/dev/null \
  || cp ~/AI/neodon-vpn/io.neodon.gui.desktop "$STAGE/desktop/"
cp ~/AI/singbox/profiles/*.json "$STAGE/profiles/"
cp ~/AI/neodon-vpn/icons/* "$STAGE/icons/" 2>/dev/null || true
cp ~/AI/neodon-vpn/flags/* "$STAGE/flags/" 2>/dev/null || true
cp /tmp/config*.example "$STAGE/examples/" 2>/dev/null || true
cp /tmp/install.sh /tmp/verify.sh "$STAGE/"
cp /tmp/sudoers-template "$STAGE/sudoers.d/neodon-vpn.template"
cd /tmp
rm -f "neodon-vpn-$VER.tar.gz" "neodon-vpn-$VER.tar.gz.sha256"
tar -czf "neodon-vpn-$VER.tar.gz" neodon-rel
sha256sum "neodon-vpn-$VER.tar.gz" > "neodon-vpn-$VER.tar.gz.sha256"
tar -tzf "neodon-vpn-$VER.tar.gz" | head -n 8
cat "neodon-vpn-$VER.tar.gz.sha256"
