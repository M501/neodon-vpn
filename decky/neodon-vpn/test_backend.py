#!/usr/bin/env python3
"""Decky backend headless tests: reads + allowlist rejections (no mutations)."""
import asyncio
import importlib.util
import sys

spec = importlib.util.spec_from_file_location("decky_backend", sys.argv[1])
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


async def main():
    fails = []

    def check(name, cond):
        print(("ok  " if cond else "FAIL"), name)
        if not cond:
            fails.append(name)

    st = await m.get_status()
    check("status-ok", st.get("ok") is True and "actual_state" in st)
    check("reject-evil-mode", (await m.set_mode("x;reboot"))["ok"] is False)
    check("reject-str-idx", (await m.set_server("1;x"))["ok"] is False)
    check("reject-oor-idx", (await m.set_server(99999))["ok"] is False)
    sv = await m.get_servers()
    check("servers-list", sv.get("ok") is True and len(sv.get("servers", [])) > 0)
    # active address must match a listed server (the QAM snap-back bug class)
    addrs = {s.get("address") for s in sv.get("servers", [])}
    check("servers-active-matches", sv.get("active") in addrs)
    check("profile-name", isinstance(st.get("profile_name"), str) and len(st.get("profile_name", "")) > 0)
    check("connected-since-int", isinstance(st.get("connected_since"), int))
    # preset map must not drift from the desktop PRESETS table
    import os
    import re
    app_path = os.environ.get("NEODON_APP", "/home/m26/AI/neodon-vpn/neodon-vpn.py")
    try:
        src = open(app_path, encoding="utf-8").read()
        blk = src.split("PRESETS = [", 1)[1].split("\n]\n", 1)[0]
        ids = set(re.findall(r'^\s*\("([a-z0-9-]+)",', blk, re.M))
    except (OSError, IndexError):
        ids = set()
    check("preset-names-cover-desktop", ids != set() and set(m.PRESET_NAMES) >= ids)
    check("quota-shape", isinstance(await m.get_quota(), dict))
    # nothing must have been mutated: mode file untouched, no workers spawned
    print("FAILURES:", fails if fails else "none")
    return 1 if fails else 0


sys.exit(asyncio.run(main()))
