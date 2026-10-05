"""Which server index does selected-server.json name? (raw.json order = grid order)"""
import json
import os

raw = json.load(open(os.path.expanduser("~/AI/neodon-sub/raw.json")))
order = [c.get("remarks") or "" for c in raw]
sel = json.load(open(os.path.expanduser("~/AI/singbox/selected-server.json")))
tag = (sel.get("tag") or "").strip()
idx = order.index(tag) if tag in order else -1
print("selected index=%d tag=%r server=%s" % (idx, tag, sel.get("server")))
print("order[%d]=%r" % (idx, order[idx] if idx >= 0 else None))
