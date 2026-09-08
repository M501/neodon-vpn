#!/usr/bin/env python3
"""One-shot: extract v2RayTun preset iconUrls -> pid url (spec 010)."""
import json

p = "C:/Users/M25/AppData/Roaming/v2RayTun.net/v2RayTun/shared_preferences.json"
d = json.load(open(p, encoding="utf-8"))
names = {"7694ec3a3d2246deb88f86b62b114c80": "ru-bez-vpn",
         "9f4ecdd2795d4cdf9a43f4802c6c94db": "popular-ai",
         "03bb08c788484515804dccdc9539648a": "social-networks",
         "67bf949591f540738d14615a75e16eab": "only-unavailable",
         "f451673995f645c0a72ca50469c92895": "ru-traffic-direct",
         "d464bf3cd9534d699152f336086074c4": "socseti-vpn",
         "e1921732c7f44526b85e3fbee48bf052": "basic-set",
         "e51e093660d04784a2328def586b2c72": "russia-mimo",
         "1d9741a7bec147ababc7cd6208d53149": "work"}
for k, v in d.items():
    if k.startswith("flutter.preset_") and isinstance(v, str) and len(v) > 100:
        try:
            pj = json.loads(v)
        except Exception:
            continue
        pid = names.get(k.split("_")[-1], "?")
        print(pid, pj.get("iconUrl", "NO-URL"))
