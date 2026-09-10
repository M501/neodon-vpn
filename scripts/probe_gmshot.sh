#!/bin/bash
# One-shot: game-mode display sockets + grim test.
echo "== wayland sockets =="
ls -la /run/user/1000/ 2>/dev/null | grep -iE "wayland|gamescope"
echo "== X sockets =="
ls -la /tmp/.X11-unix/ 2>/dev/null
echo "== steam display env =="
PID=$(pgrep -f "steam$" | head -n 1)
tr '\0' '\n' < /proc/$PID/environ 2>/dev/null | grep -E "^(DISPLAY|WAYLAND_DISPLAY|XDG_SESSION)"
echo "== grim test =="
which grim
for s in $(ls /run/user/1000/wayland-* 2>/dev/null); do
  echo "try $s"
  WAYLAND_DISPLAY=$(basename $s) XDG_RUNTIME_DIR=/run/user/1000 timeout 8 grim /tmp/gm-shot.png 2>&1
  ls -la /tmp/gm-shot.png 2>/dev/null && break
done
