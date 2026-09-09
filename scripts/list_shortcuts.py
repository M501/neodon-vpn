#!/usr/bin/env python3
"""One-shot: list non-Steam shortcuts (find Neodon appid)."""
import vdf

d = vdf.binary_load(open("/home/m26/.steam/steam/userdata/118567430/config/shortcuts.vdf", "rb"))
for k, v in d.get("shortcuts", {}).items():
    print(k, v.get("appid"), repr(v.get("AppName", ""))[:60])
