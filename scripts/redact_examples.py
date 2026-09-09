#!/usr/bin/env python3
"""Build redacted config examples (no secrets leave the host).
Replaces server/uuid/keys in vless outbounds with TEST-NET placeholders,
asserts no IPv4/UUID remains, prints only PASS/FAIL + structure stats.
Usage: redact_examples.py (writes /tmp/*.example.json)
"""
import json
import re

IPV4 = re.compile(r"^\d{1,3}(\.\d{1,3}){3}$")
UUID = re.compile(r"^[0-9a-fA-F-]{36}$")


def redact_outbound(o):
    if not isinstance(o, dict):
        return
    s = o.get("server")
    if isinstance(s, str) and (IPV4.match(s) or "." in s) and s not in ("1.1.1.1", "1.0.0.1"):
        o["server"] = "203.0.113.10"
    for k in ("uuid", "password", "private_key", "short_id", "public-key", "public_key", "token"):
        if k in o and isinstance(o[k], str) and o[k]:
            o[k] = "REDACTED"
    for v in o.values():
        if isinstance(v, dict):
            redact_outbound(v)
        elif isinstance(v, list):
            for i in v:
                redact_outbound(i)


def check_clean(o, path=""):
    bad = []
    if isinstance(o, dict):
        for k, v in o.items():
            if k in ("uuid", "password", "private_key", "short_id", "token") and isinstance(v, str) and v not in ("", "REDACTED"):
                bad.append("%s/%s" % (path, k))
            if k == "server" and isinstance(v, str) and IPV4.match(v) and v not in ("1.1.1.1", "1.0.0.1", "203.0.113.10"):
                bad.append("%s/server=%s" % (path, v))
            if k == "public-key" and isinstance(v, str) and v != "REDACTED":
                bad.append("%s/public-key" % path)
            bad += check_clean(v, "%s/%s" % (path, k))
    elif isinstance(o, list):
        for i, v in enumerate(o):
            bad += check_clean(v, "%s[%d]" % (path, i))
    elif isinstance(o, str) and UUID.match(o):
        bad.append("%s: uuid-like" % path)
    return bad


for name in ("config.json", "config-full.json", "config-proxy.json"):
    src = "/home/m26/AI/singbox/" + name
    try:
        d = json.load(open(src))
    except Exception as e:
        print(name, "SKIP", e)
        continue
    for o in d.get("outbounds", []):
        redact_outbound(o)
    bad = check_clean(d)
    assert not bad, bad
    out = "/tmp/%s.example" % name
    json.dump(d, open(out, "w"), indent=1, ensure_ascii=False)
    print(name, "PASS rules=%d outbounds=%d" % (
        len(d.get("route", {}).get("rules", [])),
        len(d.get("outbounds", []))))
