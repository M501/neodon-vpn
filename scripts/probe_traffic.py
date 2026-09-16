#!/usr/bin/env python3
"""Live egress proof: state, route, DNS, real HTTPS through TUN."""
import json
import subprocess
import urllib.request

HOME = "/home/m26"


def sh(cmd):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                       timeout=30)
    return r.stdout.strip()


st = json.loads(sh("bash %s/AI/singbox/singbox-toggle.sh status-json" % HOME))
print("STATE:", st["actual_state"], "SVC:", st["service_state"],
      "EXIT:", st["exit_ip"])
print("ROUTE1111:", sh("ip route get 1.1.1.1 | head -n 1"))
print("RESOLV:", [l for l in open("/etc/resolv.conf").read().splitlines()
                   if l.strip()][:3])
for name, url in (("IPIFY", "https://api.ipify.org"),
                  ("YT", "https://www.youtube.com/")):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=12) as r:
            print(name, r.status, "len=", len(r.read(200000)))
    except Exception as e:
        print(name, "ERR", str(e)[:120])
