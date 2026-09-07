#!/usr/bin/env python3
"""One-shot: structure of v2RayTun '.RU bez VPN' preset rules (007)."""
import json

p = "C:/Users/M25/AppData/Roaming/v2RayTun.net/v2RayTun/shared_preferences.json"
d = json.load(open(p, encoding="utf-8"))
pj = json.loads(d["flutter.preset_7694ec3a3d2246deb88f86b62b114c80"])
print("TOP-KEYS:", list(pj.keys()))


def walk(o, depth=0, path=""):
    if depth > 3:
        return
    if isinstance(o, dict):
        for k, v in o.items():
            extra = ""
            if isinstance(v, list):
                extra = "list[%d] %s" % (len(v), str(v[:3])[:160])
            elif isinstance(v, (str, int, bool)) or v is None:
                extra = str(v)[:160]
            print("  " * depth + str(k) + ": " + extra)
            if isinstance(v, (dict,)) or (isinstance(v, list) and v and isinstance(v[0], dict)):
                walk(v[0] if isinstance(v, list) else v, depth + 1, path + "/" + str(k))
    elif isinstance(o, list) and o:
        walk(o[0], depth, path)


walk(pj)
