#!/usr/bin/env python3
"""Spec 005: tunnel switches. Measured: full toggle 14s (20x serial firewall
adds ~6-8s + sleep 2 + 1s-granularity wait loop), post-switch cold egress
(DNS 864ms + first dial ~1.8s) missed by the -m 2 probe -> extra poll cycles.
Fix: patient probe during transition (marker => -m 5, steady -m 2), background
warmup curl after every service start (off the critical path), tun-poll
instead of sleep 2, 0.2s wait granularity. Killswitch stays serial (security).
Usage: patch_status_full.py <singbox-toggle.sh>; .bak-fullopt alongside.
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


# patient first probe only while transitioning (marker present)
rep('    if ip link show tun0 >/dev/null 2>&1; then tun_up=true; else tun_up=false; fi\n',
    '    if ip link show tun0 >/dev/null 2>&1; then tun_up=true; else tun_up=false; fi\n'
    '    em=2; [ -f "$TRANS_MARKER" ] && em=5\n')
rep('exit_ip=$(curl -s -m 2 https://api.ipify.org 2>/dev/null); else exit_ip=""; fi ;;',
    'exit_ip=$(curl -s -m $em https://api.ipify.org 2>/dev/null); else exit_ip=""; fi ;;')
rep('exit_ip=$(curl -s -m 2 -x socks5h://127.0.0.1:10808 https://api.ipify.org 2>/dev/null); else exit_ip=""; fi ;;',
    'exit_ip=$(curl -s -m $em -x socks5h://127.0.0.1:10808 https://api.ipify.org 2>/dev/null); else exit_ip=""; fi ;;')
# background warmup: DNS cache + REALITY session + provider path, zero critical-path cost
rep('if systemctl --user start sing-box.service; then wd_reset;',
    'if systemctl --user start sing-box.service; then (curl -s -m 12 https://api.ipify.org >/dev/null 2>&1 &); wd_reset;')
rep('if systemctl --user start sing-box-proxy.service; then wd_reset;',
    'if systemctl --user start sing-box-proxy.service; then (curl -s -m 12 -x socks5h://127.0.0.1:10808 https://api.ipify.org >/dev/null 2>&1 &); wd_reset;')
rep('    for i in $(seq 1 15); do\n'
    '      systemctl --user is-active sing-box-full.service >/dev/null 2>&1 && break\n'
    '      sleep 1\n'
    '    done',
    '    (curl -s -m 14 https://api.ipify.org >/dev/null 2>&1 &)\n'
    '    for i in $(seq 1 25); do\n'
    '      systemctl --user is-active sing-box-full.service >/dev/null 2>&1 && break\n'
    '      sleep 0.2\n'
    '    done')
rep('    sleep 2\n'
    '    if ! ip link show tun0 >/dev/null 2>&1; then',
    '    for _t in $(seq 1 15); do ip link show tun0 >/dev/null 2>&1 && break; sleep 0.2; done\n'
    '    if ! ip link show tun0 >/dev/null 2>&1; then')

T.with_name(T.name + ".bak-fullopt").write_text(T.read_text(encoding="utf-8"), encoding="utf-8")
T.write_text(src, encoding="utf-8")
bp = str(T)
if len(bp) > 2 and bp[1] == ":":
    bp = "/" + bp[0].lower() + bp[2:]
r = subprocess.run(["bash", "-n", bp], capture_output=True, text=True)
if r.returncode != 0 and sys.platform.startswith("win"):
    print("WARN bash -n skipped (win path mangling):", r.stderr.strip()[:120])
else:
    assert r.returncode == 0, r.stderr
print("FULLOPT-PATCH-OK", T)
