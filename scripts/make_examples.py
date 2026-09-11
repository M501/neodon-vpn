#!/usr/bin/env python3
"""Make sanitized config examples (placeholder outbound, no secrets)."""
import json
import os

PLACEHOLDER = {
    "tag": "proxy",
    "protocol": "vless",
    "settings": {"vnext": [{
        "address": "vpn.example.invalid",
        "port": 443,
        "users": [{"id": "00000000-0000-0000-0000-000000000000",
                   "encryption": "none", "flow": ""}],
    }]},
    "streamSettings": {"network": "tcp", "security": "none"},
}

outdir = "/tmp/neodon-examples"
os.makedirs(outdir, exist_ok=True)
for name in ("config.json", "config-full.json", "config-proxy.json"):
    d = json.load(open("/home/m26/AI/singbox/" + name))
    d["outbounds"] = [PLACEHOLDER if o.get("tag") == "proxy" else o
                      for o in d.get("outbounds", [])]
    blob = json.dumps(d, indent=2, ensure_ascii=False) + "\n"
    assert "uuid" not in blob.lower().replace('"users"', ''), name
    open(outdir + "/" + name + ".example", "w").write(blob)
    print("WROTE", name + ".example", len(blob), "bytes")
