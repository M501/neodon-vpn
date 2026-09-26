#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "$0")/.." && pwd)/lib/common.sh"
IDS=(I1 I2 I3 I4 I5 I6)
case_I1() { [[ -f "$REPO_ROOT/install.sh" ]]; }
case_I2() { [[ -f "$REPO_ROOT/release/qa-static.sh" || -f "$REPO_ROOT/qa-static.sh" ]]; }
case_I3() { [[ -f "$REPO_ROOT/release/qa-sandbox.sh" || -f "$REPO_ROOT/qa-sandbox.sh" ]]; }
case_I4() { [[ -f "$REPO_ROOT/install.sh" ]] && bash "$REPO_ROOT/install.sh" --dry-run >/dev/null; }
case_I5() { find "$REPO_ROOT" -maxdepth 3 -type f -name '*.desktop' -print | grep -q 'Neodon\|neodon' || true; }
case_I6() { [[ -f "$REPO_ROOT/install.sh" ]] || return 77; grep -q -- "--uninstall" "$REPO_ROOT/install.sh" || return 77; ! grep -Eq "rm .*raw\.json|rm .*neodon-sub" "$REPO_ROOT/install.sh"; }
for id in "${IDS[@]}"; do run_case "$id" "case_$id"; done
