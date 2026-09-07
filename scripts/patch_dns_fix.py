#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""One-shot DNS fix (2026-09-07): host DNS poisoned at ISP stub and bypasses
sing-box (127.0.0.53 loopback never enters TUN) -> no DNS-map -> TUN routing
falls back to SNI sniff, ECH/hidden-SNI sites go final-direct and die fast.
Fix: sing-box DNS remote-DoT-via-proxy + static resolv.conf via dns-fix.sh.
Steps: patch neodon-gen-config.py, install dns-fix.sh, hook toggle,
regen configs, apply dns now. Verify separately (nslookup + curl matrix).
"""
import pathlib
import shutil
import subprocess
import sys

HOME = pathlib.Path.home()
DNSFIX_SRC = pathlib.Path("/tmp/dns-fix.sh")
DNSFIX = HOME / "AI" / "singbox" / "dns-fix.sh"
GEN = HOME / "AI" / "neodon-gen-config.py"
TOGGLE = HOME / "AI" / "singbox" / "singbox-toggle.sh"


def patch(path, pairs):
    src = path.read_text(encoding="utf-8")
    for old, new in pairs:
        assert src.count(old) == 1, "%s anchor x%d: %r" % (
            path.name, src.count(old), old[:60])
        src = src.replace(old, new)
    path.write_text(src, encoding="utf-8")
    print("PATCH-OK", path.name)


# 1. gen-config DNS section
patch(GEN, [(
    '''        "dns": {
            "servers": [{"tag": "google", "type": "udp", "server": "1.1.1.1"}],
            "final": "google",
            "strategy": "ipv4_only"
        },''',
    '''        "dns": {
            "servers": [
                {"tag": "remote", "type": "tls", "server": "1.1.1.1", "detour": "proxy"},
                {"tag": "local", "type": "udp", "server": "1.1.1.1"}
            ],
            "final": "remote",
            "strategy": "ipv4_only"
        },'''), (
    '''        "route": {
            "rules": [],
            "final": preset_final,
            "auto_detect_interface": True
        }''',
    '''        "route": {
            "rules": [],
            "final": preset_final,
            "auto_detect_interface": True,
            "default_domain_resolver": "local"
        }''')])
shutil.copy(GEN, GEN.with_name("neodon-gen-config.py.bak-dns-section"))
r = subprocess.run([sys.executable, "-m", "py_compile", str(GEN)],
                   capture_output=True, text=True)
assert r.returncode == 0, r.stderr

# 2. install dns-fix.sh
shutil.copy(DNSFIX_SRC, DNSFIX)
DNSFIX.chmod(0o755)
print("INSTALLED", DNSFIX)

# 3. toggle hooks
D = "bash ~/AI/singbox/dns-fix.sh"
patch(TOGGLE, [
    ("smart) bash ~/AI/neodon-flatpak/firefox-proxy.sh restore",
     "smart) %s apply || true; bash ~/AI/neodon-flatpak/firefox-proxy.sh restore" % D),
    ("    set_mode full",
     "    %s apply || true\n    set_mode full" % D),
    ("set_mode proxy; if",
     "set_mode proxy; %s apply || true; if" % D),
    ("    set_mode off",
     "    %s restore || true\n    set_mode off" % D),
    ("stop sing-box.service && set_mode off",
     "stop sing-box.service && %s restore || true; set_mode off" % D),
    ("start sing-box.service && set_mode smart",
     "start sing-box.service && %s apply || true; set_mode smart" % D),
])
shutil.copy(TOGGLE, TOGGLE.with_name("singbox-toggle.sh.bak-dns"))
r = subprocess.run(["bash", "-n", str(TOGGLE)], capture_output=True, text=True)
assert r.returncode == 0, r.stderr
print("TOGGLE-SYNTAX-OK")

# 4. regen configs
r = subprocess.run([sys.executable, str(GEN)], capture_output=True, text=True)
print(r.stdout[-1500:])
assert "check PASS config.json" in r.stdout and \
    "check PASS config-proxy.json" in r.stdout and \
    "check PASS config-full.json" in r.stdout, "regen check failed"
print("ALL-DONE")
