#!/usr/bin/env python3
"""One-shot: dump live server remarks (spec 018 diag)."""
import json
import os

raw = json.load(open(os.path.expanduser("~/AI/neodon-sub/raw.json")))
for cfg in raw:
    for o in cfg.get("outbounds") or []:
        if o.get("protocol") == "vless":
            print(repr(cfg.get("remarks") or ""))
            break
