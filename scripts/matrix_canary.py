#!/usr/bin/env python3
"""Matrix: every profiles/*.json fragment x canary domains (spec 011).
Fragments lack 'final' — it comes from the preset global_proxy flag.
No switching, no traffic. Prints profile: domain -> outbound (how)."""
import glob
import json
import os
import re

PROF = os.path.expanduser("~/AI/singbox/profiles")
FINALS = {"default": "proxy", "ai": "proxy", "anti-censorship": "proxy",
          "ru-bez-vpn": "proxy", "russia-mimo": "proxy",
          "ru-traffic-direct": "proxy", "popular-ai": "direct",
          "social-networks": "direct", "only-unavailable": "direct",
          "socseti-vpn": "direct", "basic-set": "direct"}
DOMS = ["ya.ru", "youtube.com", "rutracker.org", "vk.com", "chatgpt.com",
        "ozon.ru", "instagram.com", "google.com"]


def load_rules(path):
    d = json.load(open(path))
    rules = d.get("rules", d.get("route", {}).get("rules", []))
    out = []
    for r in rules:
        rx = [re.compile(p) for p in r.get("domain_regex", [])] or None
        out.append((r, rx))
    return out


def match(rules, final, dom):
    dom = dom.lower().strip().rstrip(".")
    for r, rx in rules:
        if "domain" in r and dom in (x.lower() for x in r["domain"]):
            return r.get("outbound", "?"), "domain"
        if "domain_suffix" in r and any(
                dom == s.lower() or dom.endswith("." + s.lower())
                for s in r["domain_suffix"]):
            return r.get("outbound", "?"), "suffix"
        if "domain_keyword" in r and any(k.lower() in dom for k in r["domain_keyword"]):
            return r.get("outbound", "?"), "keyword"
        if rx and any(p.search(dom) for p in rx):
            return r.get("outbound", "?"), "regex"
    return final, "final"


for path in sorted(glob.glob(os.path.join(PROF, "*.json"))):
    name = os.path.splitext(os.path.basename(path))[0]
    try:
        rules = load_rules(path)
    except Exception as e:
        print("=== %s UNREADABLE %s" % (name, e))
        continue
    print("=== %s (final=%s)" % (name, FINALS.get(name, "?")))
    for d in DOMS:
        out, how = match(rules, FINALS.get(name, "?"), d)
        print("  %-14s -> %-8s (%s)" % (d, out, how))
