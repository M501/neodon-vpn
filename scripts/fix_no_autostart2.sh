#!/bin/bash
# One-shot: kill ALL VPN autostart (keep live session untouched).
export XDG_RUNTIME_DIR=/run/user/1000
export DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/1000/bus"
systemctl --user disable neodon-boot.service sing-box-proxy.service sing-box.service sing-box-full.service
echo "--- enabled? ---"
systemctl --user is-enabled neodon-boot.service sing-box-proxy.service sing-box.service sing-box-full.service
echo "--- live sing-box count (must stay 1) ---"
pgrep -c -f "sing-box run"
