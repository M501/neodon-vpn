#!/usr/bin/env python3
"""Spec 013: drop V1 presets ai/anti-censorship from apply-profile.py.
Usage: patch_drop_v1.py <apply-profile.py>; .bak-dropv1 alongside.
"""
import pathlib
import sys

T = pathlib.Path(sys.argv[1])
src = T.read_text(encoding="utf-8")


def rep(old, new, n=1):
    global src
    assert src.count(old) == n, (old[:60], src.count(old))
    src = src.replace(old, new)


rep('PROFILES = ("default", "ai", "anti-censorship", "ru-bez-vpn",',
    'PROFILES = ("default", "ru-bez-vpn",')
rep('# default/ai/anti-censorship are built-in minimal: use empty preset (BASE_HARD only via gen)',
    "# default is built-in minimal: use empty preset (BASE_HARD only via gen)")
rep("if pid in ('default', 'ai', 'anti-censorship'):",
    "if pid == 'default':")
rep('<default|ai|anti-censorship|ru-bez-vpn|',
    '<default|ru-bez-vpn|')

T.with_name(T.name + ".bak-dropv1").write_text(T.read_text(encoding="utf-8"), encoding="utf-8")
T.write_text(src, encoding="utf-8")
print("DROP-V1-OK", T)
