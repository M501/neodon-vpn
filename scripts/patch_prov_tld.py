#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""One-shot: provider bare-TLDs (ru/...) suffix-not-keyword in gen-config,
regen configs. Mirror of gen_full_profiles fix (keyword "ru" substring-matched
e.g. rutracker -> direct). Asserts anchors, py_compile, regen + check 3/3.
"""
import pathlib
import shutil
import subprocess
import sys

GEN = pathlib.Path.home() / "AI" / "neodon-gen-config.py"
shutil.copy(GEN, GEN.with_name("neodon-gen-config.py.bak-tld-kw"))
src = GEN.read_text(encoding="utf-8")
old = '''    sfx = sorted({x for x in full_direct if "." in x})
    kw = sorted({x for x in full_direct if "." not in x})'''
assert src.count(old) == 1, "anchor x%d" % src.count(old)
new = '''    sfx = sorted({x for x in full_direct
                if "." in x or x.lower() in ("ru", "рф", "xn--p1ai", "su")})
    kw = sorted({x for x in full_direct
                 if "." not in x
                 and x.lower() not in ("ru", "рф", "xn--p1ai", "su")})'''
GEN.write_text(src.replace(old, new), encoding="utf-8")
r = subprocess.run([sys.executable, "-m", "py_compile", str(GEN)],
                   capture_output=True, text=True)
assert r.returncode == 0, r.stderr
r = subprocess.run([sys.executable, str(GEN)], capture_output=True, text=True)
print(r.stdout[-1200:])
assert "check PASS config.json" in r.stdout and \
    "check PASS config-proxy.json" in r.stdout and \
    "check PASS config-full.json" in r.stdout, "regen failed"
print("TLD-FIX-OK")
