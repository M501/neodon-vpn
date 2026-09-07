#!/usr/bin/env python3
"""One-shot: v2RayTun active routing preset — where does yandex go? (007)."""
import json

p = "C:/Users/M25/AppData/Roaming/v2RayTun.net/v2RayTun/shared_preferences.json"
d = json.load(open(p, encoding="utf-8"))
print("KEYS:", [k for k in d if "rout" in k.lower() or "preset" in k.lower() or "mode" in k.lower()])
for k in d:
    if k == "flutter.settings_pref_routing_preset_enabled":
        print("ROUTING-PRESET-ENABLED:", d[k])
    if k == "flutter.settings_pref_vpn_mode":
        print("VPN-MODE:", d[k])
for k, v in d.items():
    if k.startswith("flutter.preset_") and isinstance(v, str) and len(v) > 100:
        try:
            pj = json.loads(v)
        except Exception:
            continue
        name = pj.get("name", "?")
        rules = pj.get("rules", pj.get("routing", "?"))
        blob = json.dumps(pj, ensure_ascii=False).lower()
        print("PRESET:", k[-8:], name, "| has-yandex:", ("yandex" in blob),
              "| rules-type:", type(rules).__name__,
              "| n-rules:", (len(rules) if isinstance(rules, list) else "?"))
