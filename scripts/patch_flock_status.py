#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""One-shot: status-json must not queue behind the toggle mutex (spec 002).
Read-only status takes flock -n (fail-open); mutating verbs keep flock 9.
Safe: status only reads marker/mode/profile (atomic), writes nothing.
"""
import pathlib
import subprocess

T = pathlib.Path.home() / "AI" / "singbox" / "singbox-toggle.sh"
bak = T.with_name("singbox-toggle.sh.bak-flockstatus")
bak.write_text(T.read_text(encoding="utf-8"), encoding="utf-8")

old = "exec 9>~/AI/singbox/.toggle.lock\nflock 9\n"
new = ("exec 9>~/AI/singbox/.toggle.lock\n"
       "# read-only статусы не ждут мьютекс: иначе toggle стоит в очереди\n"
       "# за медленными опросами (curl/питоны в status-json). writer'ы -\n"
       "# эксклюзив, status - fail-open (читает только marker/mode/profile).\n"
       "case \"$1\" in\n"
       "  status|status-json) flock -n 9 || true ;;\n"
       "  *) flock 9 ;;\n"
       "esac\n")
src = T.read_text(encoding="utf-8")
assert src.count(old) == 1, "flock anchor x%d" % src.count(old)
T.write_text(src.replace(old, new), encoding="utf-8")
r = subprocess.run(["bash", "-n", str(T)], capture_output=True, text=True)
assert r.returncode == 0, r.stderr
print("FLOCK-PATCH-OK backup", bak.name)
