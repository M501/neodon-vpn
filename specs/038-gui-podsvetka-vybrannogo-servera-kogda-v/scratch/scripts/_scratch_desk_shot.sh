#!/bin/bash
# Full-screen screenshot of the live Plasma session (Desktop Mode), plus a wake-up call.
set -u
export XDG_RUNTIME_DIR=/run/user/1000
export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus
export WAYLAND_DISPLAY=wayland-0
export DISPLAY=:0
export QT_QPA_PLATFORMTHEME=kde
qdbus6 org.kde.screensaver /ScreenSaver org.freedesktop.ScreenSaver.SimulateUserActivity >/dev/null 2>&1
sleep 1
rm -f /home/m26/desk.png
spectacle -f -b -n -o /home/m26/desk.png >/dev/null 2>&1
ls -la /home/m26/desk.png 2>&1
python3 - <<'EOF'
import struct
try:
    from PIL import Image
except Exception as exc:
    print("no PIL:", exc)
    raise SystemExit
im = Image.open("/home/m26/desk.png")
print("screen png size", im.size)
EOF
