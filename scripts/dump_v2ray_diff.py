#!/usr/bin/env python3
"""One-shot: diff current v2RayTun prefs vs July backup (spec 015)."""
import json

base = "C:/Users/M25/AppData/Roaming/v2RayTun.net/v2RayTun/"
now = json.load(open(base + "shared_preferences.json", encoding="utf-8"))
old = json.load(open(base + "shared_preferences.before-autoconnect-20260715-0145.json",
                     encoding="utf-8"))
for k in sorted(set(now) | set(old)):
    a, b = now.get(k, "<ABSENT>"), old.get(k, "<ABSENT>")
    sa, sb = str(a), str(b)
    if sa != sb:
        print("CHANGED:", k)
        print("  old:", sb[:200])
        print("  new:", sa[:200])
print("keys now:", len(now), "backup:", len(old))
