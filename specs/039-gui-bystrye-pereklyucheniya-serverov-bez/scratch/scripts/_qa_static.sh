#!/bin/bash
# Unpack the repo QA snapshot and run the offline (L1/L2) part of the project suite.
set -u
export XDG_RUNTIME_DIR=/run/user/1000
export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus
QA=/home/m26/AI/neodon-qa
mkdir -p "$QA"
cd "$QA" && tar xzf /home/m26/neodon-qa.tgz && echo "unpacked: $(ls | tr '\n' ' ')"

export NEODON_REPO="$QA"
echo "=== pytest (L1/L2) ==="
QT_QPA_PLATFORM=offscreen timeout 600 python3 -m pytest -q "$QA/tests" 2>&1 | tail -25

echo
echo "=== qa/run-all.sh --static ==="
NEODON_REPO="$QA" timeout 600 bash "$QA/qa/run-all.sh" --static 2>&1 | tail -30
echo
echo "=== report ==="
ls -la "$QA/qa-results/" 2>/dev/null
head -60 "$QA/qa-results/report.md" 2>/dev/null
