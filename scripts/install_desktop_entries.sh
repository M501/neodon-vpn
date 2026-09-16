#!/usr/bin/env bash
# Live-host converge: launcher + desktop + autostart + icon from /tmp drops.
# The GUI only SHOWS backend state; it never powers the VPN.
set -euo pipefail
printf '#!/bin/sh\nexec /usr/bin/python3 "$HOME/AI/neodon-vpn/neodon-vpn.py" "$@"\n' > "$HOME/.local/bin/neodon-gui"
chmod 755 "$HOME/.local/bin/neodon-gui"
install -Dm644 /tmp/nd.desktop "$HOME/.local/share/applications/io.neodon.gui.desktop"
install -Dm644 /tmp/nd.desktop "$HOME/.config/autostart/io.neodon.gui.desktop"
[ -f /tmp/nd.svg ] && install -Dm644 /tmp/nd.svg "$HOME/.local/share/icons/hicolor/scalable/apps/io.neodon.gui.svg" || true
echo DESKTOP-CONVERGED
ls -la "$HOME/.config/autostart/io.neodon.gui.desktop"
