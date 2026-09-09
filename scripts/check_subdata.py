#!/usr/bin/env python3
"""One-shot: validate backend data files for Decky panel."""
import json
import os

home = os.path.expanduser("~")
raw = json.load(open(home + "/AI/neodon-sub/raw.json"))
print("RAW:", type(raw).__name__,
      ("len=%d" % len(raw)) if isinstance(raw, list) else "")
if isinstance(raw, list) and raw:
    o = raw[0].get("outbounds") or []
    print("RAW0 outbounds:", len(o), [x.get("protocol") for x in o][:4])
    print("RAW0 remarks:", repr(raw[0].get("remarks"))[:60])
print("CACHE:", open(home + "/AI/neodon-vpn/sub-cache.json").read()[:120])
print("SEL:", open(home + "/AI/singbox/selected-server.json").read()[:160])
