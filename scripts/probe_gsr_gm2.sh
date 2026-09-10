#!/bin/bash
# One-shot: GSR with gamescope socket passthrough + ffmpeg kmsgrab fallback.
export XDG_RUNTIME_DIR=/run/user/1000 WAYLAND_DISPLAY=gamescope-0
rm -f ~/Videos/gm-test.mp4
timeout 25 flatpak run com.dec05eba.gpu_screen_recorder -w screen -c mp4 -f 60 -o ~/Videos/gm-test.mp4 >/tmp/gsr-gm2.log 2>&1 &
GSR=$!
sleep 6
kill $GSR 2>/dev/null
sleep 2
ls -la ~/Videos/gm-test.mp4 2>/dev/null || echo "GSR-FAIL"
tail -n 3 /tmp/gsr-gm2.log
echo "== kmsgrab =="
timeout 12 ffmpeg -hide_banner -f kmsgrab -i - -frames:v 1 -y /tmp/kms.png 2>&1 | tail -n 3
ls -la /tmp/kms.png 2>/dev/null || echo "KMS-FAIL"
