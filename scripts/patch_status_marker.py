#!/usr/bin/env python3
"""Spec 003c: fix TRANSITIONING deadlock — the marker shortcut sat BEFORE the
CONNECTED computation, so the cleanup line was unreachable and the marker
lived forever. Order: compute candidate first, then marker overrides anything
but CONNECTED/OFF (and is removed once reached).
Usage: patch_status_marker.py <singbox-toggle.sh>; .bak-marker alongside.
"""
import pathlib
import subprocess
import sys

T = pathlib.Path(sys.argv[1])
src = T.read_text(encoding="utf-8")


def rep(old, new, n=1):
    global src
    assert src.count(old) == n, (old[:60], src.count(old))
    src = src.replace(old, new)


rep('      if [ "$transitioning" = true ]; then\n'
    '        state=TRANSITIONING\n'
    '      elif [ "$svc_state" = "active" ] && [ "$exit_ok" = true ]; then',
    '      if [ "$svc_state" = "active" ] && [ "$exit_ok" = true ]; then')
rep('    if [ "$state" = "CONNECTED" ] || [ "$state" = "OFF" ]; then rm -f "$TRANS_MARKER"; fi\n',
    '    if [ "$transitioning" = true ] && [ "$state" != "CONNECTED" ] && [ "$state" != "OFF" ]; then\n'
    '      state=TRANSITIONING\n'
    '    else\n'
    '      rm -f "$TRANS_MARKER"\n'
    '    fi\n')

T.with_name(T.name + ".bak-marker").write_text(T.read_text(encoding="utf-8"), encoding="utf-8")
T.write_text(src, encoding="utf-8")
bp = str(T)
if len(bp) > 2 and bp[1] == ":":
    bp = "/" + bp[0].lower() + bp[2:]
r = subprocess.run(["bash", "-n", bp], capture_output=True, text=True)
if r.returncode != 0 and sys.platform.startswith("win"):
    print("WARN bash -n skipped (win path mangling):", r.stderr.strip()[:120])
else:
    assert r.returncode == 0, r.stderr
print("MARKER-PATCH-OK", T)
