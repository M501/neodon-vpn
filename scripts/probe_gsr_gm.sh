#!/bin/bash
# One-shot: 4s GSR clip in game mode (KMS, no portal), then file info.
rm -f ~/Videos/gm-test.mp4
timeout 30 flatpak run com.dec05eba.gpu_screen_recorder -w screen -c mp4 -f 60 -o ~/Videos/gm-test.mp4 >/tmp/gsr-gm.log 2>&1 &
GSR=$!
sleep 6
kill $GSR 2>/dev/null
sleep 2
ls -la ~/Videos/gm-test.mp4 2>/dev/null
tail -n 5 /tmp/gsr-gm.log
