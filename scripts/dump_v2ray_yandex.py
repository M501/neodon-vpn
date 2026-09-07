#!/usr/bin/env python3
"""One-shot: v2RayTun active preset + yandex outbound in each preset (007)."""
import json

p = "C:/Users/M25/AppData/Roaming/v2RayTun.net/v2RayTun/shared_preferences.json"
d = json.load(open(p, encoding="utf-8"))
for k in d:
    if "active" in k.lower() or "select" in k.lower() or "current" in k.lower():
        print("ACTIVE-KEY:", k, "=", str(d[k])[:160])
pl = d.get("flutter.presets")
print("PRESETS-LIST:", str(pl)[:300])


def find_yandex(obj, path=""):
    hits = []
    if isinstance(obj, dict):
        blob = json.dumps(obj, ensure_ascii=False).lower()
        if "yandex" in blob and ("outbound" in blob or "direct" in blob or "proxy" in blob):
            for rk, rv in obj.items():
                rb = json.dumps(rv, ensure_ascii=False).lower()
                if "yandex" in rb:
                    hits.append((path + "/" + str(rk), str(rv)[:200]))
        for rk, rv in obj.items():
            hits += find_yandex(rv, path + "/" + str(rk))
    elif isinstance(obj, list):
        for i, rv in enumerate(obj):
            hits += find_yandex(rv, path + "[%d]" % i)
    return hits


for k, v in d.items():
    if k.startswith("flutter.preset_") and isinstance(v, str) and len(v) > 100:
        try:
            pj = json.loads(v)
        except Exception:
            continue
        name = pj.get("name", "?")
        hits = [h for h in find_yandex(pj) if "icon" not in h[0].lower() and "logo" not in h[1].lower()]
        print("=" * 20, name)
        for h in hits[:6]:
            print("  ", h[0], "=>", h[1])
