#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Neodon full-parity profile generator (v2RayTun-clone, PROXY focus).

Supersedes gen_profiles.py (thin single-domain stubs + dead rule_set refs).
Reads v2fly dlc.dat (same lineage as v2RayTun geosite) + provider raw.json
(full 338-entry RU-direct, not first-40) and writes complete inline
sing-box profiles to ~/AI/singbox/profiles/ (backup .bak-full-DATE).

Preserved from live profiles: BASE extras (steam/hf/ozon/voice-ports),
TLD catch-all, sniff/hijack-dns, private/process/bittorrent direct.
Reference: v2RayTun shared_preferences (9 presets, vpn_mode proxy,
vpn_dns 1.1.1.1) dumped 2026-09-07.
"""
import datetime
import json
import os
import pathlib
import shutil
import sys

HOME = pathlib.Path.home()
BASE = HOME / "AI" / "singbox"
PROF_DIR = BASE / "profiles"
RAW = HOME / "AI" / "neodon-sub" / "raw.json"
DLC = pathlib.Path(os.environ.get("DLC_DAT", "/tmp/dlc.dat"))

# --- v2RayTun reference presets: (id, global_proxy, direct_specs, proxy_specs)
PRESETS = [
    ("ru-bez-vpn", True,
     ["domain:avito.st", "geosite:category-ru",
      r"regexp:.*\.ru$", r"regexp:.*\.xn--p1ai$"], []),
    ("russia-mimo", True,
     ["domain:avito.st", "geosite:category-ru", "geosite:private",
      r"regexp:.*\.ru$", r"regexp:.*\.xn--p1ai$"], []),
    ("ru-traffic-direct", True,
     ["domain:avito.st", "domain:vk.com", "geosite:category-ru",
      r"regexp:.*\.ru$", r"regexp:.*\.su$"], []),
    ("popular-ai", False, [],
     ["geosite:category-ai-!cn", "geosite:category-ai-cn"]),
    ("social-networks", False, [],
     ["geosite:discord", "geosite:github", "geosite:google", "geosite:meta",
      "geosite:openai", "geosite:spotify", "geosite:telegram",
      "geosite:tiktok", "geosite:vk", "geosite:whatsapp"]),
    ("only-unavailable", False, [],
     ["geosite:anime", "geosite:anthropic", "geosite:artstation",
      "geosite:discord", "geosite:google-gemini", "geosite:instagram",
      "geosite:linkedin", "geosite:meta", "geosite:microsoft",
      "geosite:notion", "geosite:openai", "geosite:soundcloud",
      "geosite:speedtest", "geosite:spotify", "geosite:tiktok",
      "geosite:twitch", "geosite:twitter", "geosite:youtube"]),
    ("socseti-vpn", False, [],
     ["geosite:discord", "geosite:google", "geosite:instagram",
      "geosite:openai", "geosite:spotify", "geosite:telegram",
      "geosite:tiktok", "geosite:whatsapp", "geosite:youtube"]),
    ("basic-set", False, [],
     ["domain:1e100.net", "domain:bcvcdn.com", "domain:cdninstagram.com",
      "domain:chatgpt.com", "domain:discord.com", "domain:discord.gg",
      "domain:discordapp.com", "domain:discordapp.net", "domain:fbcdn.net",
      "domain:googlevideo.com", "domain:instagram.com", "domain:tiktok.tv",
      "domain:twitch.tv", "domain:whatsapp.com", "domain:youtube.com",
      "domain:ytimg.com", "geosite:cloudflare", "geosite:discord",
      "geosite:meta", "geosite:openai", "geosite:telegram",
      "geosite:tiktok", "geosite:whatsapp", "geosite:youtube"]),
]

TLD_DIRECT = ["ru", "рф", "xn--p1ai", "su"]
EXTRA_DIRECT_STEAM_HF = ["steamcontent.com", "steamstatic.com",
                         "steampipe.akamaihd.net", "qtlglb.com", "hwcdn.net",
                         "huggingface.co", "hf.co", "cdn-lfs.huggingface.co"]
EXTRA_DIRECT_OZON = ["ozon.ru", "ozone.ru", "ozonusercontent.com"]
EXTRA_PROXY_STEAM = ["steampowered.com", "steamcommunity.com",
                     "steamgames.com"]


# --- minimal protobuf reader for GeoSiteList (no deps) ---
def _varint(buf, pos):
    shift, res = 0, 0
    while True:
        b = buf[pos]
        pos += 1
        res |= (b & 0x7F) << shift
        if not b & 0x80:
            return res, pos
        shift += 7


def _fields(buf):
    pos, end, out = 0, len(buf), []
    while pos < end:
        key, pos = _varint(buf, pos)
        fno, wire = key >> 3, key & 7
        if wire == 0:
            v, pos = _varint(buf, pos)
            out.append((fno, v))
        elif wire == 2:
            ln, pos = _varint(buf, pos)
            out.append((fno, bytes(buf[pos:pos + ln])))
            pos += ln
        else:
            raise ValueError("wire %d" % wire)
    return out


def load_dlc(path):
    raw = open(path, "rb").read()
    sites = {}
    for fno, val in _fields(raw):
        if fno != 1 or not isinstance(val, bytes):
            continue
        code, doms = None, []
        for sfno, sval in _fields(val):
            if sfno == 1:
                code = sval.decode("utf-8", "replace").lower()
            elif sfno == 2:
                dt, dv = "domain", None
                for dfno, dval in _fields(sval):
                    if dfno == 1:
                        dt = {0: "plain", 1: "regex",
                              2: "domain", 3: "full"}.get(dval, "domain")
                    elif dfno == 2:
                        dv = dval.decode("utf-8", "replace")
                if dv:
                    doms.append((dt, dv))
        if code:
            sites.setdefault(code, []).extend(doms)
    return sites


def load_provider_direct():
    data = json.loads(RAW.read_text())
    best = []
    for cfg in data:
        for r in (cfg.get("routing") or {}).get("rules", []):
            if r.get("outboundTag") == "direct" and len(r.get("domain", [])) > len(best):
                best = r["domain"]
    suffix, keyword = [], []
    for d in best:
        if d.startswith("geosite:"):
            continue  # private/category-ru covered by dump+base
        if d.startswith("domain:"):
            d = d[len("domain:"):]
        (suffix if "." in d else keyword).append(d)
    return sorted(set(suffix)), sorted(set(keyword))


def build_profile(pid, gproxy, direct_specs, proxy_specs, geo, prov_sfx, prov_kw):
    acc = {"direct": {"domain_suffix": [], "domain": [], "domain_keyword": [],
                      "domain_regex": []},
           "proxy": {"domain_suffix": [], "domain": [], "domain_keyword": [],
                     "domain_regex": []}}

    def add(side, kind, val):
        acc[side][kind].append(val)

    def expand(side, spec):
        if spec.startswith("domain:"):
            add(side, "domain_suffix", spec[len("domain:"):])
        elif spec.startswith("regexp:"):
            add(side, "domain_regex", spec[len("regexp:"):])
        elif spec.startswith("geosite:"):
            tag = spec[len("geosite:"):].lower()
            if tag == "private":
                return  # covered by geoip-private base rule
            entries = geo.get(tag)
            if entries is None:
                print("WARN %s: geosite tag missing: %s" % (pid, tag))
                return
            for dt, dv in entries:
                if dt == "domain":
                    add(side, "domain_suffix", dv)
                elif dt == "full":
                    add(side, "domain", dv)
                elif dt == "plain":
                    add(side, "domain_keyword", dv)
                elif dt == "regex":
                    add(side, "domain_regex", dv)
        else:
            raise ValueError("spec %s" % spec)

    for s in direct_specs:
        expand("direct", s)
    for s in proxy_specs:
        expand("proxy", s)
    if gproxy:  # provider RU-direct applies when final=proxy (v2RayTun merge)
        acc["direct"]["domain_suffix"].extend(prov_sfx)
        acc["direct"]["domain_keyword"].extend(prov_kw)

    for side in acc:
        for k in acc[side]:
            acc[side][k] = sorted(set(acc[side][k]))

    rules = [
        {"action": "sniff"},
        {"protocol": "dns", "action": "hijack-dns"},
        {"ip_cidr": ["10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16",
                     "127.0.0.0/8", "169.254.0.0/16", "fc00::/7",
                     "fe80::/10"], "outbound": "direct"},
        {"process_name": ["qbittorrent", "steam", "steamwebhelper", "reaper"],
         "outbound": "direct"},
        {"domain_suffix": list(EXTRA_DIRECT_STEAM_HF), "outbound": "direct"},
        {"domain_suffix": list(EXTRA_DIRECT_OZON), "outbound": "direct"},
        {"protocol": "bittorrent", "outbound": "direct"},
        {"domain_suffix": list(EXTRA_PROXY_STEAM), "outbound": "proxy"},
        {"network": "udp", "port": 3478, "outbound": "proxy"},
        {"network": "udp", "port": [4379, 4380], "outbound": "proxy"},
    ]
    for side in ("direct", "proxy"):
        out = "direct" if side == "direct" else "proxy"
        for key in ("domain_suffix", "domain", "domain_keyword",
                    "domain_regex"):
            if acc[side][key]:
                rules.append({key: acc[side][key], "outbound": out})
    rules.append({"domain_suffix": list(TLD_DIRECT), "outbound": "direct"})
    return {"rules": rules, "final": "proxy" if gproxy else "direct"}


def main():
    geo = load_dlc(str(DLC))
    prov_sfx, prov_kw = load_provider_direct()
    print("geo-tags %d provider-suffix %d provider-kw %d"
          % (len(geo), len(prov_sfx), len(prov_kw)))
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M")
    bak = BASE / ("profiles.bak-full-" + stamp)
    bak.mkdir(parents=True, exist_ok=True)
    for p in PROF_DIR.glob("*.json"):
        shutil.copy(p, bak / p.name)
    print("backup", bak)
    for pid, gproxy, direct, proxy in PRESETS:
        doc = build_profile(pid, gproxy, direct, proxy, geo, prov_sfx,
                            prov_kw)
        assert "rule_set" not in json.dumps(doc), pid
        (PROF_DIR / (pid + ".json")).write_text(
            json.dumps(doc, indent=1, ensure_ascii=False) + "\n",
            encoding="utf-8")
        n = sum(len(r.get("domain_suffix", []) + r.get("domain", []) +
                    r.get("domain_keyword", []) + r.get("domain_regex", []))
                for r in doc["rules"])
        print("wrote %s rules=%d entries~%d final=%s"
              % (pid, len(doc["rules"]), n, doc["final"]))
    # ponytail self-check: 8 files, finals match global_proxy, no rule_set
    assert len(PRESETS) == 8
    for pid, gproxy, _, _ in PRESETS:
        d = json.loads((PROF_DIR / (pid + ".json")).read_text())
        assert d["final"] == ("proxy" if gproxy else "direct"), pid
    print("SELF-CHECK OK")


if __name__ == "__main__":
    sys.exit(main())
