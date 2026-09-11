#!/usr/bin/env python3
"""One-shot: inspect live sing-box configs structure (keys/tags only)."""
import json

for name in ("config.json", "config-full.json", "config-proxy.json"):
    try:
        d = json.load(open("/home/m26/AI/singbox/" + name))
    except Exception as e:
        print(name, "ERR", e)
        continue
    obs = d.get("outbounds", [])
    print(name, "keys=", sorted(d.keys()))
    print("  outbounds=", [(o.get("tag"), o.get("protocol")) for o in obs])
    print("  has-uuid=", "uuid" in json.dumps(d))
