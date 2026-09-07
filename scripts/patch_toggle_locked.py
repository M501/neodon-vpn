#!/usr/bin/env python3
"""Spec 005b: LOCKED = REJECT present, not rules>0 (allows now persist).
Single sudo fetch reused for count + locked flag (no extra poll cost).
Usage: patch_toggle_locked.py <singbox-toggle.sh>; .bak-locked alongside.
"""
import pathlib
import subprocess
import sys

T = pathlib.Path(sys.argv[1])
src = T.read_text(encoding="utf-8")


def rep(old, new, n=1):
    global src
    assert src.count(old) == n, (old[:60], src.count(old))
    src = src.replace(old, new)


rep('    fw_rules=$(sudo -n firewall-cmd --direct --get-all-rules 2>/dev/null | wc -l)',
    '    _fw_dump=$(sudo -n firewall-cmd --direct --get-all-rules 2>/dev/null || true)\n'
    '    fw_rules=$(echo "$_fw_dump" | wc -l)\n'
    '    locked=false; echo "$_fw_dump" | grep -q \'filter OUTPUT_direct 20 \' && locked=true')
rep('      elif [ "$fw_rules" -gt 0 ]; then\n        svc_state=inactive\n        state=STOPPING',
    '      elif [ "$locked" = true ]; then\n        svc_state=inactive\n        state=STOPPING')
rep('          inactive|failed)\n            if [ "$fw_rules" -gt 0 ]; then state=LOCKED; else state=FAILED; fi',
    '          inactive|failed)\n            if [ "$locked" = true ]; then state=LOCKED; else state=FAILED; fi')
rep('if [ "$wd_status" = "locked" ] && [ "$fw_rules" -gt 0 ] && [ "$desired" != "off" ]',
    'if [ "$wd_status" = "locked" ] && [ "$locked" = true ] && [ "$desired" != "off" ]')
rep('    N=$(sudo -n firewall-cmd --direct --get-all-rules 2>/dev/null | wc -l)\n'
    '    if [ "$N" -gt 0 ]; then\n'
    '      sudo -n firewall-cmd --direct --remove-rules ipv4 filter OUTPUT_direct 2>/dev/null || true\n'
    '      sudo -n firewall-cmd --direct --remove-rules ipv6 filter OUTPUT_direct 2>/dev/null || true\n'
    '      echo "WARN: removed $N stuck rules"\n'
    '    fi',
    '    if sudo -n firewall-cmd --direct --get-all-rules 2>/dev/null | grep -q \'filter OUTPUT_direct 20 \'; then\n'
    '      bash ~/AI/singbox/killswitch.sh remove >/dev/null 2>&1 || true\n'
    '      echo "unlocked killswitch leftovers"\n'
    '    fi')

T.with_name(T.name + ".bak-locked").write_text(T.read_text(encoding="utf-8"), encoding="utf-8")
T.write_text(src, encoding="utf-8")
bp = str(T)
if len(bp) > 2 and bp[1] == ":":
    bp = "/" + bp[0].lower() + bp[2:]
r = subprocess.run(["bash", "-n", bp], capture_output=True, text=True)
if r.returncode != 0 and sys.platform.startswith("win"):
    print("WARN bash -n skipped (win path mangling):", r.stderr.strip()[:120])
else:
    assert r.returncode == 0, r.stderr
print("TOGGLE-LOCKED-OK", T)
