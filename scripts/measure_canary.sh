#!/bin/bash
# Matrix: every generated profile x canary domains (no switching, no traffic).
LOG=/tmp/canary-measure.log
: > "$LOG"
DOMS="ya.ru youtube.com rutracker.org vk.com chatgpt.com ozon.ru instagram.com google.com"
head -c 300 ~/AI/singbox/profiles/ai.json >> "$LOG" 2>&1; echo >> "$LOG"
for f in ~/AI/singbox/profiles/*.json; do
  echo "=== $(basename "$f" .json)" >> "$LOG"
  python3 /tmp/probe_routing.py "$f" $DOMS >> "$LOG" 2>&1
done
echo DONE >> "$LOG"
