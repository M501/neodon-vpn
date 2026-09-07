#!/usr/bin/env python3
"""Spec 003b: gate slow exit-probes on cheap local readiness (measured: toggle
phases total 0.75s, sing-box listens in 20ms — the 10s were 3s curl stalls x2
polls + 8s timer quantization). No port / no tun -> skip curl instantly, so
not-ready polls cost ~0.5s and the GUI burst (1.5s) detects readiness fast.
-m 1 flapped DEGRADED on a 0.78s steady egress (one live blip) -> -m 2.
Usage: patch_status_gated.py <singbox-toggle.sh>; .bak-gated alongside.
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


rep("      full|smart) exit_ip=$(curl -s -m 1 https://api.ipify.org 2>/dev/null) ;;",
    '      full|smart) if [ "$tun_up" = true ]; then exit_ip=$(curl -s -m 2 https://api.ipify.org 2>/dev/null); else exit_ip=""; fi ;;')
rep("      proxy) exit_ip=$(curl -s -m 1 -x socks5h://127.0.0.1:10808 https://api.ipify.org 2>/dev/null) ;;",
    '      proxy) if (echo > /dev/tcp/127.0.0.1/10808) 2>/dev/null; then exit_ip=$(curl -s -m 2 -x socks5h://127.0.0.1:10808 https://api.ipify.org 2>/dev/null); else exit_ip=""; fi ;;')

T.with_name(T.name + ".bak-gated").write_text(T.read_text(encoding="utf-8"), encoding="utf-8")
T.write_text(src, encoding="utf-8")
bp = str(T)
if len(bp) > 2 and bp[1] == ":":
    bp = "/" + bp[0].lower() + bp[2:]
r = subprocess.run(["bash", "-n", bp], capture_output=True, text=True)
if r.returncode != 0 and sys.platform.startswith("win"):
    print("WARN bash -n skipped (win path mangling):", r.stderr.strip()[:120])
else:
    assert r.returncode == 0, r.stderr
print("GATED-PATCH-OK", T)
