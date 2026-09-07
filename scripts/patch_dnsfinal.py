#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""One-shot v2 (2026-09-07): sing-box forbids fakeip as dns.final
('default server cannot be fakeip'). Final shape instead:
dns.rules = per-profile [direct->remote, proxy->fakeip] + catch-all
{"domain_regex": [".*"], "server": "fakeip"}; dns.final=remote (fallback).
This file: repair GEN final back to remote, append catch-all in APPLY,
regen + check 3/3. Idempotent-ish via replace-anchors.
"""
import pathlib
import subprocess
import sys

HOME = pathlib.Path.home()
GEN = HOME / "AI" / "neodon-gen-config.py"
APPLY = HOME / "AI" / "singbox" / "apply-profile.py"
CATCHALL = ' + [{"domain_regex": [".*"], "server": "fakeip"}]'


def patch(path, pairs):
    src = path.read_text(encoding="utf-8")
    for old, new in pairs:
        assert src.count(old) == 1, "%s anchor x%d: %r" % (
            path.name, src.count(old), old[:70])
        src = src.replace(old, new)
    path.write_text(src, encoding="utf-8")
    print("PATCH-OK", path.name)


gen_src = GEN.read_text(encoding="utf-8")
if '"final": "fakeip"' in gen_src:
    GEN.write_text(gen_src.replace('"final": "fakeip"',
                                   '"final": "remote"'),
                   encoding="utf-8")
    print("GEN final repaired remote")
else:
    print("GEN final already remote")

ap_src = APPLY.read_text(encoding="utf-8")
if '"domain_regex": [".*"]' in ap_src:
    print("APPLY catch-all present, SKIP")
else:
    patch(APPLY, [(
        '''        dns["rules"] = prof.get("dns_rules", [])''',
        '''        dns["rules"] = prof.get("dns_rules", [])%s''' % CATCHALL)])
    r = subprocess.run([sys.executable, "-m", "py_compile", str(APPLY)],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr

for p in (GEN, APPLY):
    r = subprocess.run([sys.executable, "-m", "py_compile", str(p)],
                       capture_output=True, text=True)
    assert r.returncode == 0, (p.name, r.stderr)
r = subprocess.run([sys.executable, str(GEN)], capture_output=True, text=True)
print(r.stdout[-800:])
assert "check PASS config.json" in r.stdout and \
    "check PASS config-proxy.json" in r.stdout and \
    "check PASS config-full.json" in r.stdout, "regen failed"
print("DNS-CATCHALL-OK")
