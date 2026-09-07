#!/usr/bin/env bash
# qa-motion.sh — on-demand motion-QA capture (Bazzite/KDE, GSR Flatpak via KMS).
# BATTERY CONTRACT (портатив!): никакого демона/автозапуска/крона. Каждый запуск
# пишет РОВНО один mp4 (секунды, не минуты) и завершается сам (timeout).
# GSR-процессов между запусками быть не должно: проверяется pgrep в конце.
# Использование: qa-motion.sh <seconds:3-15> <tag>
# Выход: ~/Videos/neodon-qa-<tag>-<ts>.mp4 + PTS-jank сводка + 1 кадр jpg.
# Анализ на Windows: sftp get + vision_analyze(frame) + ffprobe csv по желанию.
set -u
SEC="${1:-5}"; TAG="${2:-manual}"
case "$SEC" in ''|*[!0-9]*) echo "seconds must be 3-15"; exit 2;; esac
[ "$SEC" -ge 3 ] && [ "$SEC" -le 15 ] || { echo "seconds must be 3-15"; exit 2; }
export XDG_RUNTIME_DIR=/run/user/1000 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus WAYLAND_DISPLAY=wayland-0
TS=$(date +%Y%m%d-%H%M%S)
OUT=~/Videos/neodon-qa-${TAG}-${TS}.mp4
timeout $SEC flatpak run --command=gpu-screen-recorder com.dec05eba.gpu_screen_recorder \
  -w screen -c mp4 -f 60 -o "$OUT" >/dev/null 2>&1
[ -f "$OUT" ] || { echo "CAPTURE-FAIL (no file)"; exit 1; }
DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT" 2>/dev/null)
JANK=$(ffprobe -v error -select_streams v:0 -show_entries packet=pts_time -of csv=p=0 "$OUT" 2>/dev/null \
  | python3 -c 'import sys; t=[float(x) for x in sys.stdin.read().split() if x];
print("frames=%d gaps>100ms=%d maxgap=%.0fms" % (len(t), sum(1 for a,b in zip(t,t[1:]) if (b-a)*1000>100), (max([b-a for a,b in zip(t,t[1:])]) if len(t)>1 else 0)*1000))')
ffmpeg -y -v error -i "$OUT" -vframes 1 -vf scale=640:-1 "${OUT%.mp4}.jpg" 2>/dev/null
echo "FILE: $OUT dur=${DUR}s $JANK"
pgrep -f gpu-screen-recorder >/dev/null && echo "WARN: gsr still alive" || echo "GSR-OFF (battery ok)"
