#!/usr/bin/env python3
"""Spec 015 (converge): drop russia-mimo/ru-traffic-direct from whitelists.
Usage: patch_drop_dup.py <file>. Asserts at least one replacement.
"""
import pathlib
import sys

T = pathlib.Path(sys.argv[1])
src = T.read_text(encoding="utf-8")
n0 = len(src)
src = src.replace("russia-mimo|", "")
src = src.replace("ru-traffic-direct|", "")
src = src.replace('"russia-mimo", ', "")
src = src.replace('"ru-traffic-direct", ', "")
src = src.replace("'russia-mimo', ", "")
src = src.replace("'ru-traffic-direct', ", "")
assert len(src) != n0, "nothing matched in %s" % T
T.write_text(src, encoding="utf-8")
print("DROP-DUP-OK", T)
