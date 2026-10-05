#!/bin/bash
# Stage 1: backup live GUI, verify deployed md5, probe geometry of the NEW build.
set -u
GUIF=/home/m26/AI/neodon-vpn/neodon-vpn.py
if [ ! -f "${GUIF}.pre038" ]; then
  cp "$GUIF" "${GUIF}.pre038"
  echo "backup created: ${GUIF}.pre038"
else
  echo "backup already exists"
fi
echo "live md5: $(md5sum "$GUIF" | cut -d' ' -f1)"
echo "=== selected-server.json before ==="
cat /home/m26/AI/singbox/selected-server.json
echo
echo "=== offscreen geometry probe (new build) ==="
QT_QPA_PLATFORM=offscreen python3 /tmp/width_live.py 2>/dev/null | tail -25
echo "=== frame-detector self-check on the OLD grab ==="
python3 /tmp/frames.py /home/m26/win_before.png 2>&1 | tail -6
