#!/usr/bin/env python3
import json
sel = json.load(open("/home/m26/AI/singbox/selected-server.json"))
print("SEL:", sel)
raw = json.load(open("/home/m26/AI/neodon-sub/raw.json"))
print("N:", len(raw))
for i, cfg in enumerate(raw):
    for o in cfg.get("outbounds") or []:
        if o.get("protocol") == "vless":
            s = ((o.get("settings") or {}).get("vnext") or [{}])[0]
            print(i, repr(cfg.get("remarks")), "->", repr(s.get("address")))
            break
