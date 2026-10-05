"""Final anchor hygiene: drop orphan closings, close whatever stays open."""
import os
import re
import sys

os.chdir(os.path.dirname(os.path.abspath(__file__)) + "/..")

ANCHOR_OPEN = re.compile(r"^\s*<!--\s*ANCHOR:([a-z0-9-]+)\s*-->\s*$")
ANCHOR_CLOSE = re.compile(r"^\s*<!--\s*/ANCHOR:([a-z0-9-]+)\s*-->\s*$")

for doc in ("spec.md", "plan.md", "tasks.md", "implementation-summary.md"):
    with open(doc, encoding="utf-8", newline="") as f:
        lines = f.read().replace("\r\n", "\n").split("\n")
    out, open_ids = [], []
    dropped = []
    for ln in lines:
        mo, mc = ANCHOR_OPEN.match(ln), ANCHOR_CLOSE.match(ln)
        if mo:
            open_ids.append(mo.group(1))
        elif mc:
            if mc.group(1) in open_ids:
                open_ids.remove(mc.group(1))
            else:
                dropped.append((mc.group(1), len(out) + 1))
                continue
        out.append(ln)
    for anchor in open_ids:
        out.append("<!-- /ANCHOR:%s -->" % anchor)
        print("%s: closed open anchor %s" % (doc, anchor))
    with open(doc, "w", encoding="utf-8", newline="") as f:
        f.write("\n".join(out))
    if dropped:
        print("%s: dropped orphan closings %s" % (doc, dropped))
    if not dropped and not open_ids:
        print("%s: anchors balanced" % doc)
file_failed = False
sys.exit(0)
