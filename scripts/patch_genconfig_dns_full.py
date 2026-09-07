#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""One-shot host surgery on ~/AI/neodon-gen-config.py (2026-09-07):
1. DNS 8.8.8.8 -> 1.1.1.1 (killswitch allowlist + v2RayTun parity vpn_dns).
2. Provider RU-direct: first-40 truncation -> FULL list (suffix+keyword split).
Backs up orig, asserts single-match replaces, py_compile, regenerates configs.
"""
import pathlib
import shutil
import subprocess
import sys

P = pathlib.Path.home() / "AI" / "neodon-gen-config.py"
bak = P.with_name("neodon-gen-config.py.bak-dns-full")
shutil.copy(P, bak)

src = P.read_text(encoding="utf-8")

old_dns = '"server": "8.8.8.8"'
assert src.count(old_dns) == 1, "dns anchor x%d" % src.count(old_dns)
src = src.replace(old_dns, '"server": "1.1.1.1"')

old_block = '''    plain_direct = []
    for d in prov_domains:
        if d.startswith("domain:"):
            continue
        if d.startswith("geosite:"):
            continue
        # plain domain
        plain_direct.append(d)
        if len(plain_direct) >= 40:  # limit
            break
    if plain_direct:
        rules.append({"domain_suffix": plain_direct, "outbound": "direct"})'''
assert src.count(old_block) == 1, "provider anchor missing"

new_block = '''    full_direct = []
    for d in prov_domains:
        if d.startswith("geosite:"):
            continue  # private/category-ru covered by base rules + profiles
        if d.startswith("domain:"):
            d = d[len("domain:"):]
        full_direct.append(d)
    sfx = sorted({x for x in full_direct if "." in x})
    kw = sorted({x for x in full_direct if "." not in x})
    if sfx:
        rules.append({"domain_suffix": sfx, "outbound": "direct"})
    if kw:
        rules.append({"domain_keyword": kw, "outbound": "direct"})'''
src = src.replace(old_block, new_block)

P.write_text(src, encoding="utf-8")
r = subprocess.run([sys.executable, "-m", "py_compile", str(P)],
                   capture_output=True, text=True)
assert r.returncode == 0, r.stderr
print("PATCH-OK backup", bak.name)

r = subprocess.run([sys.executable, str(P)], capture_output=True, text=True)
print(r.stdout[-2000:])
print(r.stderr[-1000:] if r.returncode else "GEN-OK")
