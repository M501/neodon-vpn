#!/bin/bash
# Neodon GUI diagnostics: live-window grab + per-page horizontal-range probe.
set -u
GUIFILE=/home/m26/AI/neodon-vpn/neodon-vpn.py

echo "=== process ==="
ps -o pid,lstart,cmd -C python3 | grep -F "$GUIFILE" || echo "no live GUI"
echo "=== file mtime ==="
stat -c '%y %n' "$GUIFILE"

echo "=== grab live window ==="
rm -f /home/m26/win_before.png
printf '%s' '{"action":"grab","path":"/home/m26/win_before.png"}' > /home/m26/AI/neodon-vpn/gui-action.json
sleep 4
ls -la /home/m26/win_before.png 2>&1 || echo "GRAB FAILED"

echo "=== widths probe (offscreen) ==="
QT_QPA_PLATFORM=offscreen python3 /tmp/probe_widths.py > /home/m26/probe.json 2>/home/m26/probe.err
echo "probe rc=$?"
python3 /tmp/sum.py 2>&1 || tail -12 /home/m26/probe.err
