#!/usr/bin/env python3
"""Soak probe: backend state before/after 60s idle, no panel involved."""
import json
import subprocess
import time


def state():
    out = subprocess.run(["bash", "/home/m26/AI/singbox/singbox-toggle.sh",
                          "status-json"], capture_output=True, text=True,
                         timeout=60).stdout
    d = json.loads(out)
    return d["actual_state"], d["service_state"], d["exit_ip"]


def restarts():
    out = subprocess.run(["systemctl", "--user", "show", "sing-box.service",
                          "-p", "NRestarts", "--value"],
                         capture_output=True, text=True, timeout=15).stdout
    return out.strip()


a = state()
r0 = restarts()
time.sleep(60)
b = state()
r1 = restarts()
print("BEFORE:", a)
print("AFTER: ", b)
print("RESTARTS:", r0, "->", r1)
print("SOAK:", "OK" if a[0] == b[0] == "CONNECTED" and r0 == r1 == "0" else "CHECK")
