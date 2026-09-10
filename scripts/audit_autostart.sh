#!/bin/bash
# One-shot READ-ONLY audit: everything that could auto-start VPN.
echo "== user units enabled? =="
systemctl --user is-enabled sing-box.service sing-box-full.service neodon-gui.service 2>&1
echo "== system units enabled? =="
systemctl is-enabled sing-box.service sing-box-full.service neodon-vpn.service 2>&1 | head -n 4
echo "== desktop autostart files? =="
ls ~/.config/autostart/ 2>/dev/null | grep -iE "neodon|vpn|sing" || echo NONE
echo "== watchdog logic (toggle script) =="
grep -nE "watchdog|desired|auto|reconnect|retry" ~/AI/singbox/singbox-toggle.sh | head -n 20
echo "== install.sh enable lines =="
grep -nE "enable|disable" C:/AI/Hermes_PROJECTS/bazzite/projects/neodon-vpn/install.sh 2>/dev/null | head -n 8
ls ~/AI/neodon-vpn/install.sh 2>/dev/null
