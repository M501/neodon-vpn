#!/usr/bin/env python3
"""Spec 005c: narrow DNS allows to dport 53 (the broad '-d 1.1.1.1 ACCEPT'
let ANY app bypass the TUN via 1.1.1.1:443 — real leak path, found by the
first (flawed) forced-egress probe). Migrate broad rules once (grep-local,
zero sudo when clean) + prune stale endpoint ACCEPTs (unbounded growth:
39 rules and counting). Fail-closed order untouched.
Usage: patch_ks_dnsnarrow.py <killswitch.sh>; .bak-dnsnarrow alongside.
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


rep('  "ipv4 4 -d 1.1.1.1 -j ACCEPT"\n'
    '  "ipv4 4 -d 1.0.0.1 -j ACCEPT"\n',
    '  "ipv4 4 -p udp -d 1.1.1.1 --dport 53 -j ACCEPT"\n'
    '  "ipv4 4 -p tcp -d 1.1.1.1 --dport 53 -j ACCEPT"\n'
    '  "ipv4 4 -p udp -d 1.0.0.1 --dport 53 -j ACCEPT"\n'
    '  "ipv4 4 -p tcp -d 1.0.0.1 --dport 53 -j ACCEPT"\n')
rep('  EXISTING="$($FW --get-all-rules 2>/dev/null || true)"\n',
    '  EXISTING="$($FW --get-all-rules 2>/dev/null || true)"\n'
    '  # one-time migration: drop pre-narrowing broad DNS allows\n'
    '  for broad in "ipv4 filter OUTPUT_direct 4 -d 1.1.1.1 -j ACCEPT" "ipv4 filter OUTPUT_direct 4 -d 1.0.0.1 -j ACCEPT"; do\n'
    '    if grep -qF -- "$broad" <<<"$EXISTING"; then\n'
    '      set -- $broad\n'
    '      $FW --remove-rule "$1" filter OUTPUT_direct "$2" "${@:3}" 2>/dev/null || true\n'
    '      EXISTING="$(echo "$EXISTING" | grep -vF -- "$broad" || true)"\n'
    '    fi\n'
    '  done\n'
    '  # prune endpoint ACCEPTs that are no longer current (unbounded growth)\n'
    '  for stale in $(echo "$EXISTING" | grep -o \'ipv4 filter OUTPUT_direct 5 -d [0-9.]* -j ACCEPT\' | awk \'{print $6}\'); do\n'
    '    keep=false\n'
    '    for ip in $ips; do [ "$stale" = "$ip" ] && keep=true; done\n'
    '    if [ "$keep" = false ]; then\n'
    '      $FW --remove-rule ipv4 filter OUTPUT_direct 5 -d "$stale" -j ACCEPT 2>/dev/null || true\n'
    '    fi\n'
    '  done\n')

T.with_name(T.name + ".bak-dnsnarrow").write_text(T.read_text(encoding="utf-8"), encoding="utf-8")
T.write_text(src, encoding="utf-8")
bp = str(T)
if len(bp) > 2 and bp[1] == ":":
    bp = "/" + bp[0].lower() + bp[2:]
r = subprocess.run(["bash", "-n", bp], capture_output=True, text=True)
if r.returncode != 0 and sys.platform.startswith("win"):
    print("WARN bash -n skipped (win path mangling):", r.stderr.strip()[:120])
else:
    assert r.returncode == 0, r.stderr
print("KS-DNSNARROW-OK", T)
