#!/usr/bin/env python3
"""One-shot: clash API in sing-box configs? route rule counts? (spec 007)."""
import glob
import json

for c in ("config.json", "config-full.json", "config-proxy.json"):
    try:
        d = json.load(open("/home/m26/AI/singbox/" + c))
    except Exception as e:
        print(c, "UNREADABLE", e)
        continue
    exp = d.get("experimental", {})
    rules = d.get("route", {}).get("rules", [])
    outs = [o.get("tag") for o in d.get("outbounds", [])]
    print(c, "| experimental:", list(exp.keys()) or "none",
          "| route-rules:", len(rules), "| outbounds:", outs)
