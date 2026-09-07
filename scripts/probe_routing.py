#!/usr/bin/env python3
"""Deterministic routing oracle: match domains against a sing-box config's
route.rules (first match wins, else final). No traffic. Usage:
probe_routing.py <config.json> <domain> [domain...]
Matches sing-box semantics for domain/domain_suffix/domain_keyword/domain_regex.
"""
import json
import re
import sys

cfg = json.load(open(sys.argv[1]))
rules = cfg["route"]["rules"]
final = cfg["route"].get("final", "?")

# precompile regex rules once
compiled = []
for r in rules:
    if "domain_regex" in r:
        compiled.append((r, [re.compile(p) for p in r["domain_regex"]]))
    else:
        compiled.append((r, None))


def match(dom):
    dom = dom.lower().strip().rstrip(".")
    for r, rx in compiled:
        if "domain" in r and dom in (d.lower() for d in r["domain"]):
            return r.get("outbound", "?"), "domain"
        if "domain_suffix" in r and any(
                dom == s.lower() or dom.endswith("." + s.lower())
                for s in r["domain_suffix"]):
            return r.get("outbound", "?"), "suffix"
        if "domain_keyword" in r and any(k.lower() in dom for k in r["domain_keyword"]):
            return r.get("outbound", "?"), "keyword"
        if rx is not None and any(p.search(dom) for p in rx):
            return r.get("outbound", "?"), "regex"
    return final, "final"


for d in sys.argv[2:]:
    out, how = match(d)
    print("%-28s -> %-8s (%s)" % (d, out, how))
