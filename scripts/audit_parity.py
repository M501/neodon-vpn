#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Neodon traffic-rules parity audit: Windows v2RayTun reference vs live host.
Runs ON HOST (data local). Checks:
 1. gen_full_profiles.PRESETS == WINDOWS_SPECS (verified dump 2026-09-07)
 2. profiles/*.json on disk == rebuilt from specs (multiset-equal rules)
 3. legacy default sane (final, no rule_set refs)
 4. provider RU-direct fully covered in ru-bez-vpn (via check_routes sim)
 5. no thin leftovers (entry thresholds), no rule_set refs anywhere
Exit 0 = AUDIT-OK, 1 = diffs printed.
"""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path.home() / "AI"))
import gen_full_profiles as G
import check_routes as CR

HOME = pathlib.Path.home()
PROF = HOME / "AI" / "singbox" / "profiles"

# Verified 2026-09-07 from shared_preferences.json (v2RayTun Windows).
WINDOWS_SPECS = {
    "ru-bez-vpn": (True,
                   ["domain:avito.st", "geosite:category-ru",
                    r"regexp:.*\.ru$", r"regexp:.*\.xn--p1ai$"], []),
    "russia-mimo": (True,
                    ["domain:avito.st", "geosite:category-ru",
                     "geosite:private", r"regexp:.*\.ru$",
                     r"regexp:.*\.xn--p1ai$"], []),
    "ru-traffic-direct": (True,
                          ["domain:avito.st", "domain:vk.com",
                           "geosite:category-ru", r"regexp:.*\.ru$",
                           r"regexp:.*\.su$"], []),
    "popular-ai": (False, [],
                   ["geosite:category-ai-!cn", "geosite:category-ai-cn"]),
    "social-networks": (False, [],
                        ["geosite:discord", "geosite:github", "geosite:google",
                         "geosite:meta", "geosite:openai", "geosite:spotify",
                         "geosite:telegram", "geosite:tiktok", "geosite:vk",
                         "geosite:whatsapp"]),
    "only-unavailable": (False, [],
                         ["geosite:anime", "geosite:anthropic",
                          "geosite:artstation", "geosite:discord",
                          "geosite:google-gemini", "geosite:instagram",
                          "geosite:linkedin", "geosite:meta",
                          "geosite:microsoft", "geosite:notion",
                          "geosite:openai", "geosite:soundcloud",
                          "geosite:speedtest", "geosite:spotify",
                          "geosite:tiktok", "geosite:twitch",
                          "geosite:twitter", "geosite:youtube"]),
    "socseti-vpn": (False, [],
                    ["geosite:discord", "geosite:google",
                     "geosite:instagram", "geosite:openai",
                     "geosite:spotify", "geosite:telegram",
                     "geosite:tiktok", "geosite:whatsapp",
                     "geosite:youtube"]),
    "basic-set": (False, [],
                  ["domain:1e100.net", "domain:bcvcdn.com",
                   "domain:cdninstagram.com", "domain:chatgpt.com",
                   "domain:discord.com", "domain:discord.gg",
                   "domain:discordapp.com", "domain:discordapp.net",
                   "domain:fbcdn.net", "domain:googlevideo.com",
                   "domain:instagram.com", "domain:tiktok.tv",
                   "domain:twitch.tv", "domain:whatsapp.com",
                   "domain:youtube.com", "domain:ytimg.com",
                   "geosite:cloudflare", "geosite:discord", "geosite:meta",
                   "geosite:openai", "geosite:telegram", "geosite:tiktok",
                   "geosite:whatsapp", "geosite:youtube"]),
}

MIN_ENTRIES = {"ru-bez-vpn": 1000, "russia-mimo": 1000,
               "ru-traffic-direct": 1000, "popular-ai": 200,
               "social-networks": 1500, "only-unavailable": 1500,
               "socseti-vpn": 1000, "basic-set": 800}


def sig(rule):
    """Order-insensitive signature of a routing rule (matchers+outbound)."""
    m = []
    for k in ("domain_suffix", "domain", "domain_keyword", "domain_regex",
              "ip_cidr", "process_name", "protocol"):
        if k in rule:
            v = rule[k]
            m.append((k, tuple(sorted(v)) if isinstance(v, list) else v))
    extra = {k: (tuple(sorted(v)) if isinstance(v, list) else v)
             for k, v in rule.items()
             if k not in ("domain_suffix", "domain", "domain_keyword",
                          "domain_regex", "ip_cidr", "process_name",
                          "protocol", "outbound") or k == "outbound"}
    return (tuple(sorted(m)), rule.get("outbound") or "",
            tuple(sorted((k, str(v)) for k, v in rule.items()
                         if k in ("action", "network", "port"))))


def entries(doc):
    n = 0
    for r in doc["rules"]:
        for k in ("domain_suffix", "domain", "domain_keyword",
                  "domain_regex"):
            v = r.get(k, [])
            n += len(v) if isinstance(v, list) else 1
    return n


def main():
    fails = []
    # 1. specs == windows reference
    cur = {pid: (g, d, p) for pid, g, d, p in G.PRESETS}
    if cur != WINDOWS_SPECS:
        fails.append("PRESETS drift vs WINDOWS_SPECS: %s" %
                     sorted(set(cur) ^ set(WINDOWS_SPECS)))
    else:
        print("1. specs == windows reference: OK (8 presets)")
    # 2. disk == rebuilt
    geo = G.load_dlc(str(pathlib.Path(
        __import__("os").environ.get("DLC_DAT",
                                     str(HOME / "AI/singbox/geosite-dlc.dat")))))
    prov_sfx, prov_kw = G.load_provider_direct()
    for pid, gproxy, direct, proxy in G.PRESETS:
        exp = G.build_profile(pid, gproxy, direct, proxy, geo, prov_sfx,
                              prov_kw)
        disk = json.loads((PROF / (pid + ".json")).read_text(
            encoding="utf-8"))
        es = sorted(sig(r) for r in exp["rules"])
        ds = sorted(sig(r) for r in disk["rules"])
        if es != ds or exp["final"] != disk["final"]:
            fails.append("%s: disk != rebuilt (rules %d/%d final %s/%s)"
                         % (pid, len(ds), len(es), disk["final"],
                            exp["final"]))
        else:
            print("2. %-16s disk==rebuilt OK rules=%d entries~%d" %
                  (pid, len(ds), entries(disk)))
    # 3. legacy sanity
    for pid in ("default",):
        d = json.loads((PROF / (pid + ".json")).read_text(encoding="utf-8"))
        blob = json.dumps(d)
        ok = bool(d.get("final")) and "rule_set" not in blob
        print("3. legacy %-14s final=%s rules=%d %s"
              % (pid, d.get("final"), len(d.get("rules", [])),
                 "OK" if ok else "SUSPECT"))
        if not ok:
            fails.append(pid + " legacy suspect")
    # 4. provider coverage in ru-bez-vpn
    rb = json.loads((PROF / "ru-bez-vpn.json").read_text(encoding="utf-8"))
    drules = [r for r in rb["rules"] if r.get("outbound") == "direct"]
    uncovered = [d for d in prov_sfx + prov_kw
                 if not any(CR.match(r, d) for r in drules)]
    print("4. provider coverage in ru-bez-vpn: %d/%d (%s)" %
          (len(prov_sfx) + len(prov_kw) - len(uncovered),
           len(prov_sfx) + len(prov_kw),
           "OK" if not uncovered else "MISS %s" % uncovered[:10]))
    if uncovered:
        fails.append("provider uncovered: %s" % uncovered[:10])
    # 5. thresholds + no rule_set
    for pid, minimum in MIN_ENTRIES.items():
        d = json.loads((PROF / (pid + ".json")).read_text(encoding="utf-8"))
        n, blob = entries(d), json.dumps(d)
        ok = n >= minimum and "rule_set" not in blob
        print("5. %-16s entries=%d (min %d) %s"
              % (pid, n, minimum, "OK" if ok else "THIN/SRS"))
        if not ok:
            fails.append(pid + " thin or rule_set")
    if fails:
        print("AUDIT-FAIL (%d):" % len(fails))
        for f in fails:
            print(" -", f)
        return 1
    print("AUDIT-OK: parity holds")
    return 0


if __name__ == "__main__":
    sys.exit(main())
