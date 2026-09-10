#!/bin/bash
# One-shot: disable VPN autostart (units stay running this session).
export XDG_RUNTIME_DIR=/run/user/1000
export DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/1000/bus"
systemctl --user disable sing-box.service sing-box-full.service
echo "---"
systemctl --user is-enabled sing-box.service sing-box-full.service
echo "---"
systemctl --user is-active sing-box.service sing-box-full.service
