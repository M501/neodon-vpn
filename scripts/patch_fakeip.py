#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""One-shot FakeIP wiring (2026-09-07): ECH hides SNI on TUN; IP->domain map
collides on shared anycast IPs -> wrong outbound. Fix: proxy-side domains
resolve to FakeIP (unambiguous binding).
1. neodon-gen-config.py: dns += fakeip server, independent_cache, rules:[].
2. apply-profile.py: write profile dns_rules into dns.rules (absent -> []).
3. Regen 3 configs + check. Profiles (with dns_rules) come from updated
   gen_full_profiles.py run separately. Verify separately (canary TLS1.3).
"""
import pathlib
import shutil
import subprocess
import sys

HOME = pathlib.Path.home()
GEN = HOME / "AI" / "neodon-gen-config.py"
APPLY = HOME / "AI" / "singbox" / "apply-profile.py"


def patch(path, pairs):
    src = path.read_text(encoding="utf-8")
    for old, new in pairs:
        assert src.count(old) == 1, "%s anchor x%d: %r" % (
            path.name, src.count(old), old[:70])
        src = src.replace(old, new)
    path.write_text(src, encoding="utf-8")
    print("PATCH-OK", path.name)


shutil.copy(GEN, GEN.with_name("neodon-gen-config.py.bak-fakeip"))
gen_src = GEN.read_text(encoding="utf-8")
if '"independent_cache": True' in gen_src and '"fakeip"' in gen_src:
    print("GEN already patched, SKIP")
else:
    gen_src = gen_src.replace('"independent_cache": true',
                              '"independent_cache": True')
    GEN.write_text(gen_src, encoding="utf-8")
    print("GEN true->True repaired")
    if '"fakeip"' not in gen_src:
        patch(GEN, [(
        '''                {"tag": "remote", "type": "tls", "server": "1.1.1.1", "detour": "proxy"},
                {"tag": "local", "type": "udp", "server": "1.1.1.1"}
            ],
            "final": "remote",
            "strategy": "ipv4_only"''',
        '''                {"tag": "remote", "type": "tls", "server": "1.1.1.1", "detour": "proxy"},
                {"tag": "local", "type": "udp", "server": "1.1.1.1"},
                {"tag": "fakeip", "type": "fakeip", "inet4_range": "198.18.0.0/15", "inet6_range": "fc00::/18"}
            ],
            "rules": [],
            "final": "remote",
            "independent_cache": True,
            "strategy": "ipv4_only"''')])
    r = subprocess.run([sys.executable, "-m", "py_compile", str(GEN)],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr

shutil.copy(APPLY, APPLY.with_name("apply-profile.py.bak-fakeip"))
patch(APPLY, [(
    '''            route["rules"] = rs''',
    '''            route["rules"] = rs
        dns = data.setdefault("dns", {})
        dns["rules"] = prof.get("dns_rules", [])''')])
r = subprocess.run([sys.executable, "-m", "py_compile", str(APPLY)],
                   capture_output=True, text=True)
assert r.returncode == 0, r.stderr

r = subprocess.run([sys.executable, str(GEN)], capture_output=True, text=True)
print(r.stdout[-1200:])
assert "check PASS config.json" in r.stdout and \
    "check PASS config-proxy.json" in r.stdout and \
    "check PASS config-full.json" in r.stdout, "regen failed"
print("FAKEIP-WIRING-OK")
