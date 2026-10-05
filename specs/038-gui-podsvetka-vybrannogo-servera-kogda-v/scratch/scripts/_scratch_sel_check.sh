#!/bin/bash
# What does the GUI's active-server detection read, under the selector topology?
echo "=== outbound tags in config.json ==="
python3 - <<'PY'
import json, os
for f in ("config.json", "config-proxy.json", "config-full.json"):
    p = os.path.expanduser("~/AI/singbox/" + f)
    try:
        d = json.load(open(p))
    except Exception as exc:
        print(f, "ERR", exc)
        continue
    for o in d.get("outbounds", []):
        if o.get("tag") in ("proxy", "auto"):
            keys = {k: o[k] for k in ("type", "server", "server_port", "outbounds", "default", "interrupt_exist_connections") if k in o}
            print(f, o["tag"], json.dumps(keys, ensure_ascii=False)[:220])
PY
echo "=== selected-server.json ==="
cat ~/AI/singbox/selected-server.json
echo
echo "=== raw.json entries (index -> address) ==="
python3 - <<'PY'
import json, os
p = os.path.expanduser("~/AI/neodon-sub/raw.json")
try:
    d = json.load(open(p))
except Exception as exc:
    raise SystemExit("raw.json ERR %s" % exc)
items = d if isinstance(d, list) else d.get("servers") or []
for i, s in enumerate(items):
    print(i, s.get("remarks"), s.get("address"), s.get("port"))
PY
