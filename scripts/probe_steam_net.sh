#!/bin/bash
# One-shot: Steam process net env (proxy?) + Steam proxy config.
PID=$(pgrep -f "steam$" | head -n 1)
echo "PID=$PID"
tr '\0' '\n' < /proc/$PID/environ 2>/dev/null | grep -iE "proxy|wayland|display" | sed -E "s/=(.{12}).*/=<set>/"
echo "== vdf proxy =="
grep -i -A3 -B1 "proxy" ~/.local/share/Steam/config/config.vdf 2>/dev/null | head -n 12
echo "== steam netns check =="
readlink /proc/$PID/ns/net
readlink /proc/self/ns/net
