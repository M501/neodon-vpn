#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Offline first-match simulator for Neodon sing-box profiles.
Usage: check_routes.py <profile-id> <domain> [domain...]
Prints outbound per domain using the same rule order sing-box applies.
Covers: domain_suffix / domain / domain_keyword / domain_regex.
Skips: action/sniff/hijack (non-routing), ip_cidr/process/protocol/port
(non-domain rules). Falls back to profile final.
"""
import json
import pathlib
import re
import sys

BASE = pathlib.Path.home() / "AI" / "singbox" / "profiles"


def match(rule, dom):
    if "domain_suffix" in rule:
        if any(dom == s or dom.endswith("." + s) or
               ("." not in s and dom.endswith(s)) for s in rule["domain_suffix"]):
            return True
    if "domain" in rule:
        if dom in rule["domain"]:
            return True
    if "domain_keyword" in rule:
        if any(k in dom for k in rule["domain_keyword"]):
            return True
    if "domain_regex" in rule:
        if any(re.search(p, dom) for p in rule["domain_regex"]):
            return True
    return False


def main():
    pid, doms = sys.argv[1], sys.argv[2:]
    prof = json.loads((BASE / (pid + ".json")).read_text(encoding="utf-8"))
    for d in doms:
        out = None
        for r in prof["rules"]:
            if "outbound" not in r or "action" in r:
                continue
            if any(k in r for k in ("domain_suffix", "domain",
                                    "domain_keyword", "domain_regex")):
                if match(r, d):
                    out = r["outbound"]
                    break
        print("%s -> %s" % (d, out or prof.get("final", "?") + " (final)"))


if __name__ == "__main__":
    main()
