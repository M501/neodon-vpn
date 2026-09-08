#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Apply routing profile to smart/proxy configs. Validates, sing-box check, atomic apply, restart. Full config untouched."""
import json, os, sys, shutil, subprocess, pathlib
HOME = pathlib.Path.home()
BASE = HOME / 'AI' / 'singbox'
# PROFILES extended by upload_profiles.py
PROFILES = ("default", "ru-bez-vpn", "popular-ai", "social-networks", "only-unavailable", "socseti-vpn", "basic-set")
CONFIGS = ['config.json', 'config-proxy.json']  # full not touched
SB = '/usr/local/bin/sing-box'
def load_profile(pid):
    p = BASE / 'profiles' / f'{pid}.json'
    if not p.exists():
        # default is built-in minimal: use empty preset (BASE_HARD only via gen)
        # For MVP, if file missing, treat as empty rules with final proxy
        if pid == 'default':
            return {'rules': [], 'final': 'proxy'}
        print(f'profile not found: {p}', file=sys.stderr)
        sys.exit(1)
    return json.loads(p.read_text())

def apply(pid, check_only=False):
    prof = load_profile(pid)
    rules = prof.get('rules') or []
    final = prof.get('final') or 'proxy'
    # Build full route rules: BASE is handled inside profile json already (includes BASE_HARD etc)
    # So rules from profile ARE the complete route.rules
    for name in CONFIGS:
        path = BASE / name
        if not path.exists():
            continue
        data = json.loads(path.read_text())
        route = data.setdefault('route', {})
        # backup
        bak = path.with_suffix('.bak')
        shutil.copy(path, bak)
        old_rules = route.get('rules')
        old_final = route.get('final')
        # For these configs, route.rules is fully replaced by profile rules + provider logic
        # But our generated configs already have provider+BASE_HARD rules. Profile rules ARE already complete.
        # For MVP: replace route.rules/rules with profile rules if profile has rules, else keep existing
        # Actually preset profiles already contain BASE_HARD+preset+BASE_RU -> complete. So replace.
        route.setdefault("rule_set", [])
        if rules:
            route["rules"] = rules
            route["final"] = final
        else:
            rs=route.get("rules") or []
            route["rules"] = rs
        dns = data.setdefault("dns", {})
        dns["rules"] = prof.get("dns_rules", [])
        dns = data.setdefault("dns", {})
        dns["rules"] = prof.get("dns_rules", [])
        # validate sing-box check
        tmp = path.with_suffix('.tmp')
        tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False))
        res = subprocess.run([SB, 'check', '-c', str(tmp)], capture_output=True, text=True)
        if res.returncode != 0:
            print(f"sing-box check failed for {name}: {res.stderr[:800]}", file=sys.stderr)
            tmp.unlink(missing_ok=True)
            # rollback
            shutil.copy(bak, path)
            if check_only:
                print(json.dumps({"profile": pid, "check": "failed", "config": name, "error": res.stderr[:500]}))
                sys.exit(1)
            else:
                sys.exit(1)
        if check_only:
            tmp.unlink(missing_ok=True)
            continue
        tmp.replace(path)
        print(f"applied {pid} to {name}")
    if check_only:
        print(json.dumps({"profile": pid, "check": "passed"}))
        return
    # persist active profile
    (BASE / '.profile').write_text(pid)
    # restart active service
    import subprocess as sp
    for svc in ['sing-box.service', 'sing-box-proxy.service']:
        r = sp.run(['systemctl', '--user', 'is-active', svc], capture_output=True, text=True)
        if r.stdout.strip() == 'active':
            sp.run(['systemctl', '--user', 'restart', svc])
            print(f"restarted {svc}")
            break
    print(json.dumps({"profile": pid, "applied": True}))

if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser(description='usage: apply-profile.py [--check] <default|ru-bez-vpn|popular-ai|social-networks|only-unavailable|socseti-vpn|basic-set>')
    ap.add_argument('profile', nargs='?', help='profile id')
    ap.add_argument('--check', action='store_true', help='validate only')
    args = ap.parse_args()
    if not args.profile:
        ap.print_help()
        sys.exit(2)
    if args.profile not in PROFILES:
        print(f"unknown profile {args.profile}, expected one of {PROFILES}", file=sys.stderr)
        sys.exit(2)
    apply(args.profile, check_only=args.check)