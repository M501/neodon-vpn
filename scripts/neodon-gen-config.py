#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate sing-box configs from provider raw.json (v2ray format) to sing-box 1.13 format.
Produces config.json (smart: mixed+tun), config-proxy.json (mixed only), config-full.json (tun only).
Mimics BASE_HARD + BASE_RU + provider RU list. No external geosite.db needed (inline rules).
"""
import json, os, sys, pathlib

HOME = pathlib.Path.home()
BASE = HOME / "AI" / "singbox"
RAW = HOME / "AI" / "neodon-sub" / "raw.json"
# Also check alternative SD path
if not RAW.exists():
    RAW = pathlib.Path("/run/media/m26/0000-D182/neodon-vpn/raw.json")

def load_raw():
    if not RAW.exists():
        print(f"RAW not found: {RAW}", file=sys.stderr)
        sys.exit(1)
    data = json.loads(RAW.read_text())
    if not isinstance(data, list) or not data:
        print("invalid raw.json", file=sys.stderr)
        sys.exit(1)
    return data

def build_outbound(cfg):
    # find vless outbound
    for o in cfg.get("outbounds") or []:
        if o.get("protocol") != "vless":
            continue
        vnext = (o.get("settings") or {}).get("vnext") or [{}]
        s = vnext[0]
        user = (s.get("users") or [{}])[0]
        st = o.get("streamSettings") or {}
        out = {
            "type": "vless",
            "tag": "proxy",
            "server": s.get("address"),
            "server_port": s.get("port"),
            "uuid": user.get("id"),
        }
        flow = user.get("flow") or ""
        if flow:
            out["flow"] = flow
        # transport
        net = st.get("network") or "tcp"
        if net == "ws":
            ws = st.get("wsSettings") or {}
            headers = ws.get("headers") or {}
            host = headers.get("Host") or ws.get("host") or ""
            transport = {"type": "ws", "path": ws.get("path") or "/"}
            if host:
                transport["headers"] = {"Host": host}
            out["transport"] = transport
        elif net == "grpc":
            gs = st.get("grpcSettings") or {}
            transport = {"type": "grpc", "service_name": gs.get("serviceName") or "grpc"}
            out["transport"] = transport
        # tls/reality
        sec = st.get("security") or "none"
        if sec == "reality":
            rs = st.get("realitySettings") or {}
            out["tls"] = {
                "enabled": True,
                "server_name": rs.get("serverName") or s.get("address"),
                "utls": {"enabled": True, "fingerprint": rs.get("fingerprint") or "chrome"},
                "reality": {
                    "enabled": True,
                    "public_key": rs.get("publicKey") or "",
                    "short_id": rs.get("shortId") or ""
                }
            }
        elif sec == "tls":
            ts = st.get("tlsSettings") or {}
            out["tls"] = {
                "enabled": True,
                "server_name": ts.get("serverName") or s.get("address"),
                "utls": {"enabled": True, "fingerprint": ts.get("fingerprint") or "chrome"}
            }
            if ts.get("alpn"):
                out["tls"]["alpn"] = ts.get("alpn")
        # security none -> no tls
        return out
    raise ValueError("no vless outbound found")

def domain_to_rule(domain_entry):
    """Convert provider domain entry like 'domain:ru' or 'geosite:private' or 'ozon.ru' to sing-box rule fragment."""
    # provider list contains entries like "domain:ru", "geosite:private", "ozon.ru"
    if domain_entry.startswith("domain:"):
        val = domain_entry[len("domain:"):]
        # val like "ru", "рф", "xn--p1ai", "su"
        # treat as geosite? For short TLD like ru, use domain_suffix
        return {"domain_suffix": [val]}
    if domain_entry.startswith("geosite:"):
        tag = domain_entry[len("geosite:"):]
        # map known tags to inline? For now, return rule_set reference (but we won't have .srs)
        # Instead, return None to skip, and let BASE_RU handle RU. For private, skip (already handled)
        if tag == "private":
            return None
        if tag == "category-ru":
            return {"rule_set": ["geosite-ru"]}  # will need .srs, but we can replace with domain_suffix ru
            # fallback to domain_suffix
        # For unknown, try to map to domain_suffix if possible, else skip
        return None
    # plain domain like "ozon.ru"
    # check if it contains dot
    if "." in domain_entry:
        return {"domain_suffix": [domain_entry]}
    else:
        # single word like "yandex" -> domain_keyword?
        return {"domain_keyword": [domain_entry]}

def build_route_rules(provider_cfg, preset_rules=None):
    """Build route rules for smart/proxy."""
    rules = []
    # sniff + hijack-dns (sing-box actions)
    rules.append({"action": "sniff"})
    rules.append({"protocol": "dns", "action": "hijack-dns"})
    # private IPs direct
    rules.append({"ip_cidr": ["10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16", "127.0.0.0/8", "169.254.0.0/16", "fc00::/7", "fe80::/10"], "outbound": "direct"})
    # process direct
    rules.append({"process_name": ["qbittorrent", "steam", "steamwebhelper", "reaper"], "outbound": "direct"})
    # ozon direct (critical)
    rules.append({"domain_suffix": ["ozon.ru", "ozone.ru", "ozonusercontent.com"], "outbound": "direct"})
    # bittorrent direct
    rules.append({"protocol": "bittorrent", "outbound": "direct"})
    # provider RU domains -> direct (extract from provider routing.rules[1].domain)
    # Find provider's large domain list
    prov_domains = []
    for r in provider_cfg.get("routing", {}).get("rules", []):
        if "domain" in r and r.get("outboundTag") == "direct":
            prov_domains = r["domain"]
            break
    # Convert first 30 domains as domain_suffix to avoid huge config, plus ensure ru/рф handling
    # For MVP, add domain_suffix for plain domains and geosite:category-ru handling
    # Instead of converting all 200, add a few key suffixes that cover RU
    # Add generic RU suffixes
    rules.append({"domain_suffix": ["ru", "рф", "xn--p1ai", "su"], "outbound": "direct"})
    # Also add yandex etc as direct via domain_suffix for key ones
    # We'll add a broad rule: if domain contains yandex, mail.ru etc -> direct (but we already have ru suffix covers yandex.ru)
    # For provider's explicit list, add domain_suffix for entries that are plain domains
    full_direct = []
    for d in prov_domains:
        if d.startswith("geosite:"):
            continue  # private/category-ru covered by base rules + profiles
        if d.startswith("domain:"):
            d = d[len("domain:"):]
        full_direct.append(d)
    sfx = sorted({x for x in full_direct if "." in x})
    kw = sorted({x for x in full_direct if "." not in x})
    if sfx:
        rules.append({"domain_suffix": sfx, "outbound": "direct"})
    if kw:
        rules.append({"domain_keyword": kw, "outbound": "direct"})
    # preset rules (if provided, they are already sing-box format with domain_suffix/rule_set etc)
    if preset_rules:
        rules.extend(preset_rules)
    # RU ip direct (geoip-ru) -> use ip_cidr for RU? We don't have list, but we can add a placeholder
    # Use 0.0.0.0/1? No. Better skip ip geo, rely on domain rules. For test, domain rules enough.
    # Final fallback is proxy (if global_proxy) else direct - handled via route.final
    return rules

def build_config(outbound, provider_cfg, with_tun, with_mixed, preset_final="proxy"):
    # ponytail: minimal 1.13-compatible format — sniff as route rule, dns type udp, no dns outbound
    cfg = {
        "log": {"level": "info"},
        "dns": {
            "servers": [
                {"tag": "remote", "type": "tls", "server": "1.1.1.1", "detour": "proxy"},
                {"tag": "local", "type": "udp", "server": "1.1.1.1"}
            ],
            "final": "remote",
            "strategy": "ipv4_only"
        },
        "inbounds": [],
        "outbounds": [
            outbound,
            {"type": "direct", "tag": "direct"},
            {"type": "block", "tag": "block"}
        ],
        "route": {
            "rules": [],
            "final": preset_final,
            "auto_detect_interface": True,
            "default_domain_resolver": "local"
        }
    }
    if with_mixed:
        cfg["inbounds"].append({
            "type": "mixed",
            "tag": "mixed-in",
            "listen": "127.0.0.1",
            "listen_port": 10808
        })
    if with_tun:
        cfg["inbounds"].append({
            "type": "tun",
            "tag": "tun-in",
            "interface_name": "tun0",
            "address": "172.19.0.1/30",
            "mtu": 9000,
            "auto_route": True,
            "strict_route": False,
            "stack": "system"
        })
    # route rules
    # For full (tun only) with preset_final proxy, we want minimal rules: just private/bypass + final proxy (ignore presets)
    # But for smart/proxy, use full rules
    # Determine if this is full: with_tun and not with_mixed
    is_full = with_tun and not with_mixed
    if is_full:
        # minimal for full: only private + final proxy, no preset, no RU bypass (everything via VPN)
        cfg["route"]["rules"] = [
            {"action": "sniff"},
            {"protocol": "dns", "action": "hijack-dns"},
            {"ip_cidr": ["10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16", "127.0.0.0/8"], "outbound": "direct"}
        ]
        cfg["route"]["final"] = "proxy"
    else:
        # smart/proxy: full routing with provider RU + preset support
        # For now without preset, final proxy
        rules = build_route_rules(provider_cfg, preset_rules=None)
        cfg["route"]["rules"] = rules
        cfg["route"]["final"] = preset_final
    return cfg

def main():
    data = load_raw()
    # Use first server as default (index 0)
    idx = 0
    # Check if selected-server.json exists to pick index
    sel_path = BASE / "selected-server.json"
    if sel_path.exists():
        try:
            sel = json.loads(sel_path.read_text())
            # sel contains server address, try to find matching index
            srv = sel.get("server")
            for i, cfg in enumerate(data):
                for o in cfg.get("outbounds") or []:
                    if o.get("protocol") == "vless":
                        addr = ((o.get("settings") or {}).get("vnext") or [{}])[0].get("address")
                        if addr == srv:
                            idx = i
                            break
                else:
                    continue
                break
        except:
            pass
    print(f"Using provider index {idx} remarks={data[idx].get('remarks')}")
    outbound = build_outbound(data[idx])
    print(f"Outbound: {outbound['server']}:{outbound['server_port']} tls={bool(outbound.get('tls'))}")
    BASE.mkdir(parents=True, exist_ok=True)
    # config.json: smart (mixed+tun)
    cfg_smart = build_config(outbound, data[idx], with_tun=True, with_mixed=True, preset_final="proxy")
    # config-proxy.json: proxy only (mixed)
    cfg_proxy = build_config(outbound, data[idx], with_tun=False, with_mixed=True, preset_final="proxy")
    # config-full.json: tun only
    cfg_full = build_config(outbound, data[idx], with_tun=True, with_mixed=False, preset_final="proxy")
    for name, cfg in [("config.json", cfg_smart), ("config-proxy.json", cfg_proxy), ("config-full.json", cfg_full)]:
        path = BASE / name
        path.write_text(json.dumps(cfg, indent=2, ensure_ascii=False) + "\n")
        print(f"Wrote {path} ({len(json.dumps(cfg))} bytes)")
        # check
        import subprocess
        res = subprocess.run(["/usr/local/bin/sing-box", "check", "-c", str(path)], capture_output=True, text=True)
        if res.returncode == 0:
            print(f"  check PASS {name}")
        else:
            print(f"  check FAIL {name}: {res.stderr[:800]}")
            print(f"  stdout: {res.stdout[:800]}")
    # also write selected-server.json if not exists
    if not sel_path.exists():
        sel = {"tag": data[idx].get("remarks") or outbound["server"], "server": outbound["server"], "server_port": outbound["server_port"], "updated": "2026-08-26T00:00:00"}
        sel_path.write_text(json.dumps(sel, indent=2, ensure_ascii=False) + "\n")
        print(f"Wrote {sel_path}")

if __name__ == "__main__":
    main()
