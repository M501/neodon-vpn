#!/usr/bin/env python3
"""One-shot verify: no dup names in whitelists, hostctl works, audit parity."""
import subprocess

for f in ("/home/m26/AI/neodon-hostctl", "/home/m26/AI/singbox/apply-profile.py"):
    blob = open(f, encoding="utf-8", errors="replace").read()
    bad = [n for n in ("russia-mimo", "ru-traffic-direct") if n in blob]
    print(("DIRTY " if bad else "CLEAN ") + f + " " + ",".join(bad))
import ast
ast.parse(open("/home/m26/AI/singbox/apply-profile.py", encoding="utf-8").read())
print("APPLY-SYNTAX-OK")
r = subprocess.run(["bash", "/home/m26/AI/neodon-hostctl", "profile", "russia-mimo"],
                   capture_output=True, text=True)
print("REJECT-RC:", r.returncode, r.stderr.strip()[:80])
r = subprocess.run(["python3", "/home/m26/AI/singbox/apply-profile.py", "--check", "ru-bez-vpn"],
                   capture_output=True, text=True)
print("CHECK-RC:", r.returncode, (r.stdout + r.stderr).strip()[:200])
