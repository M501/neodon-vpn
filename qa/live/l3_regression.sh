#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "$0")/.." && pwd)/lib/common.sh"
IDS=(L1 L2 L3 L4 L5)
if ! require_live; then for id in "${IDS[@]}"; do skip_case "$id" "NEODON_LIVE=1 not set"; done; exit 0; fi

case_L1() { [[ -x "$BACKEND_ROOT/qa-gui-states.sh" || -x "$REPO_ROOT/qa-gui-states.sh" ]]; }
case_L2() {
  local s="$BACKEND_ROOT/qa-gui-states.sh"
  [[ -x "$s" ]] || s="$REPO_ROOT/qa-gui-states.sh"
  [[ -x "$s" ]] || return 1
  bash "$s"
}
case_L3() {
  python3 - <<'PY'
import pathlib
roots=[pathlib.Path.home()/"AI/neodon-vpn", pathlib.Path.home()/"AI/singbox"]
needle=("Traceback", "syntax error")
found=[]
for root in roots:
    if not root.exists():
        continue
    for p in root.rglob("*.log"):
        try: t=p.read_text(errors="ignore")
        except OSError: continue
        for x in needle:
            if x in t: found.append((str(p),x))
assert not found, found
PY
}
case_L4() { bash -n "$BACKEND_ROOT/singbox-toggle.sh" "$BACKEND_ROOT/singbox-server.sh" "$BACKEND_ROOT/killswitch.sh" "$BACKEND_ROOT/dns-fix.sh"; }
case_L5() { python3 -m py_compile "$BACKEND_ROOT/apply-profile.py" "$REPO_ROOT/neodon-vpn.py"; }
for id in "${IDS[@]}"; do run_case "$id" "case_$id"; done
