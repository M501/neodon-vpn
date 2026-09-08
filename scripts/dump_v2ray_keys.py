#!/usr/bin/env python3
"""One-shot: v2RayTun full key list + active routing preset (spec 015)."""
import json

p = "C:/Users/M25/AppData/Roaming/v2RayTun.net/v2RayTun/shared_preferences.json"
d = json.load(open(p, encoding="utf-8"))
print("TOTAL-KEYS:", len(d))
for k in sorted(d):
    v = d[k]
    s = str(v)
    print("%-55s %s" % (k, s[:100]))
