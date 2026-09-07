#!/usr/bin/env python3
"""Spec 005b: killswitch remove() drops only REJECT (2 calls, 0.6s). The
allowlist is static: without REJECT it is a harmless subset of the default
ACCEPT policy, so re-adding ~20-40 rules on every full-toggle (9.4s measured)
is pure waste. Fail-closed order (allows -> verify -> REJECT LAST) untouched.
Usage: patch_ks_rejectonly.py <killswitch.sh>; .bak-rejectonly alongside.
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


rep('remove() {\n'
    '  $FW --remove-rules ipv4 filter OUTPUT_direct 2>/dev/null || true\n'
    '  $FW --remove-rules ipv6 filter OUTPUT_direct 2>/dev/null || true\n'
    '  echo "KILLSWITCH: firewall removed"\n'
    '}',
    'remove() {\n'
    '  # allows persist by design (harmless without REJECT); only REJECT is dynamic\n'
    '  $FW --remove-rule ipv4 filter OUTPUT_direct 20 -j REJECT 2>/dev/null || true\n'
    '  $FW --remove-rule ipv6 filter OUTPUT_direct 20 -j REJECT 2>/dev/null || true\n'
    '  echo "KILLSWITCH: unlocked (allowlist persists)"\n'
    '}')

T.with_name(T.name + ".bak-rejectonly").write_text(T.read_text(encoding="utf-8"), encoding="utf-8")
T.write_text(src, encoding="utf-8")
bp = str(T)
if len(bp) > 2 and bp[1] == ":":
    bp = "/" + bp[0].lower() + bp[2:]
r = subprocess.run(["bash", "-n", bp], capture_output=True, text=True)
if r.returncode != 0 and sys.platform.startswith("win"):
    print("WARN bash -n skipped (win path mangling):", r.stderr.strip()[:120])
else:
    assert r.returncode == 0, r.stderr
print("KS-REJECTONLY-OK", T)
