#!/usr/bin/env python3
"""One-shot: dedup Neodon VPN Steam shortcuts, keep first (spec 024)."""
import shutil
import vdf

P = "/home/m26/.steam/steam/userdata/118567430/config/shortcuts.vdf"
shutil.copy(P, "/tmp/shortcuts.vdf.predup")
d = vdf.binary_load(open(P, "rb"))
seen = False
out = {}
for k in sorted(d.get("shortcuts", {}), key=int):
    v = d["shortcuts"][k]
    if v.get("AppName") == "Neodon VPN" and not seen:
        seen = True
        out[k] = v
    elif v.get("AppName") == "Neodon VPN":
        continue
    else:
        out[k] = v
# reindex 0..n
d["shortcuts"] = {str(i): v for i, v in enumerate(out.values())}
vdf.binary_dump(d, open(P, "wb"))
kept = sum(1 for v in d["shortcuts"].values() if v.get("AppName") == "Neodon VPN")
print("DEDUP-OK kept=%d total=%d" % (kept, len(d["shortcuts"])))
