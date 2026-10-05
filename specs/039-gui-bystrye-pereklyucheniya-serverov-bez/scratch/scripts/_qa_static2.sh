#!/bin/bash
# Full suite run against the LIVE GUI file: unpack, pytest, static QA, report.
set -u
QA=/home/m26/AI/neodon-qa
LIVE_GUI=/home/m26/AI/neodon-vpn/neodon-vpn.py
rm -rf "$QA"; mkdir -p "$QA"; cd "$QA" || exit 1
tar xzf /home/m26/neodon-qa.tgz
export NEODON_REPO="$QA"
export NEODON_APP="$LIVE_GUI"
export QT_QPA_PLATFORM=offscreen

echo "=== pytest (L1/L2) against $LIVE_GUI ==="
timeout 600 python3 -m pytest -q "$QA/tests" 2>&1 | tail -18

echo
echo "=== qa/run-all.sh --static ==="
NEODON_REPO="$QA" timeout 600 bash "$QA/qa/run-all.sh" --static 2>&1 | tail -22

echo
echo "=== report ==="
cat "$QA/qa-results/report.md" 2>/dev/null | head -30
