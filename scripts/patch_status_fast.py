#!/usr/bin/env python3
"""Spec 003: status-json must stop blocking polls (measured 4.6s/transition poll:
curl -m 3 exit-probe x2 timeouts + 2s TCP latency probe), TRANS_MARKER must
survive toggle exit (honest Switching pill), ON-claim moves to GUI CONNECTED.
Usage: patch_status_fast.py <singbox-toggle.sh>; keeps .bak-fastpoll alongside.
Safe: asserts every anchor count, bash -n after.
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


# exit-probes: worst case 3s stall each -> 1s (hysteresis in GUI covers blips)
rep("exit_ip=$(curl -s -m 3 https://api.ipify.org 2>/dev/null) ;;",
    "exit_ip=$(curl -s -m 1 https://api.ipify.org 2>/dev/null) ;;")
rep("exit_ip=$(curl -s -m 3 -x socks5h://127.0.0.1:10808 https://api.ipify.org 2>/dev/null) ;;",
    "exit_ip=$(curl -s -m 1 -x socks5h://127.0.0.1:10808 https://api.ipify.org 2>/dev/null) ;;")
# full-mode readiness probe: 8s stall -> 3s
rep("EXIT=$(curl -s -m 8 https://api.ipify.org 2>/dev/null)",
    "EXIT=$(curl -s -m 3 https://api.ipify.org 2>/dev/null)")
# per-poll TCP latency probe: 2s stall -> 1s (display-only metric)
rep("socket.create_connection((p['server'], p['server_port']), timeout=2).close()",
    "socket.create_connection((p['server'], p['server_port']), timeout=1).close()")
# marker was deleted by toggle's own EXIT trap 0.8s after press, so polls never
# saw TRANSITIONING; it must live until CONNECTED/OFF is actually reached
rep('    trap \'rm -f "$TRANS_MARKER"\' EXIT INT TERM\n', '')
rep('    server_tag=$(python3 -c',
    '    if [ "$state" = "CONNECTED" ] || [ "$state" = "OFF" ]; then rm -f "$TRANS_MARKER"; fi\n'
    '    server_tag=$(python3 -c')
# ON-claim at press moment lied (service starts in 0.8s, exit ready in ~10s);
# script reports switching, GUI notifies on real CONNECTED
rep('echo "VPN SMART ON"; notify "VPN SMART ON"',
    'echo "VPN SMART switching..."; notify "переключение на SMART…"')
rep('echo "VPN PROXY ON"; notify "VPN PROXY ON"',
    'echo "VPN PROXY switching..."; notify "переключение на PROXY…"')

T.with_name(T.name + ".bak-fastpoll").write_text(T.read_text(encoding="utf-8"), encoding="utf-8")
T.write_text(src, encoding="utf-8")
bp = str(T)
if len(bp) > 2 and bp[1] == ":":
    bp = "/" + bp[0].lower() + bp[2:]  # C:/x -> /c/x for git-bash/MSYS
r = subprocess.run(["bash", "-n", bp], capture_output=True, text=True)
assert r.returncode == 0, r.stderr
print("FASTPOLL-PATCH-OK", T)
