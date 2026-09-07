#!/usr/bin/env python3
"""Spec 009: desktop notification spam off (owner request 2026-09-08).
Neuters notify() in singbox-toggle.sh and the inline server-switch ping in
singbox-server.sh. Echos/CLI output untouched. Usage: patch_notify_off.py <file>.
"""
import pathlib
import subprocess
import sys

T = pathlib.Path(sys.argv[1])
src = T.read_text(encoding="utf-8")
n0 = len(src)
src = src.replace(
    'notify() { notify-send "VPN" "$1" 2>/dev/null || true; }',
    'notify() { :; }  # owner 2026-09-08: desktop popup spam off')
src = src.replace(
    'notify-send "VPN" "Сервер: $name" 2>/dev/null || true',
    ':')
assert len(src) != n0, "no notify-send source found in %s" % T
T.with_name(T.name + ".bak-notifyoff").write_text(
    pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"), encoding="utf-8")
T.write_text(src, encoding="utf-8")
bp = str(T)
if len(bp) > 2 and bp[1] == ":":
    bp = "/" + bp[0].lower() + bp[2:]
r = subprocess.run(["bash", "-n", bp], capture_output=True, text=True)
if r.returncode != 0 and sys.platform.startswith("win"):
    print("WARN bash -n skipped (win path mangling)")
else:
    assert r.returncode == 0, r.stderr
print("NOTIFYOFF-OK", T)
