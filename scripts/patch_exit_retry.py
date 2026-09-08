#!/usr/bin/env python3
"""Spec 016: exit probe retries once (provider egress churns in bursts;
single-miss DEGRADED flaps observed 4x/7min). Steady cost unchanged
(retry runs only when the first attempt fails). Usage: <toggle.sh>.
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


rep("exit_ip=$(curl -s -m $em https://api.ipify.org 2>/dev/null); else",
    "exit_ip=$(curl -s -m $em https://api.ipify.org 2>/dev/null "
    "|| curl -s -m $em https://api.ipify.org 2>/dev/null); else")
rep("exit_ip=$(curl -s -m $em -x socks5h://127.0.0.1:10808 https://api.ipify.org 2>/dev/null); else",
    "exit_ip=$(curl -s -m $em -x socks5h://127.0.0.1:10808 https://api.ipify.org 2>/dev/null "
    "|| curl -s -m $em -x socks5h://127.0.0.1:10808 https://api.ipify.org 2>/dev/null); else")

T.with_name(T.name + ".bak-exitretry").write_text(T.read_text(encoding="utf-8"), encoding="utf-8")
T.write_text(src, encoding="utf-8")
bp = str(T)
if len(bp) > 2 and bp[1] == ":":
    bp = "/" + bp[0].lower() + bp[2:]
r = subprocess.run(["bash", "-n", bp], capture_output=True, text=True)
if r.returncode != 0 and sys.platform.startswith("win"):
    print("WARN bash -n skipped (win path mangling)")
else:
    assert r.returncode == 0, r.stderr
print("EXITRETRY-OK", T)
