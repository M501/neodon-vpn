"""Diff the 039 docs against their Level templates: header order and anchors."""
import os
import re

os.chdir(os.path.dirname(os.path.abspath(__file__)) + "/..")

DOCS = ["spec.md", "plan.md", "tasks.md", "implementation-summary.md"]


def headers(text):
    return [h.strip() for h in re.findall(r"(?m)^## +(.+)$", text)]


def anchors(text):
    return re.findall(r"<!--\s*ANCHOR:([a-z0-9-]+)\s*-->", text)


def load(path):
    with open(path, encoding="utf-8", newline="") as f:
        return f.read().replace("\r\n", "\n")


for doc in DOCS:
    tpl = os.path.join("scratch", doc.replace(".md", ".template.md"))
    mine_p = doc
    if not os.path.exists(tpl) or not os.path.exists(mine_p):
        print("%-26s (no template copy, skipped)" % doc)
        continue
    tpl_txt, mine_txt = load(tpl), load(mine_p)
    tpl_h, mine_h = headers(tpl_txt), headers(mine_txt)
    # expected order check (indexOf with cursor semantics)
    cursor, missing = 0, []
    for want in tpl_h:
        if want.startswith(("L2:", "FIX ADDENDUM")):
            pass
        try:
            idx = mine_h.index(want, cursor)
            cursor = idx + 1
        except ValueError:
            missing.append(want)
    tpl_a = set(anchors(tpl_txt))
    mine_a = set(anchors(mine_txt))
    print("=== %s" % doc)
    print("   missing/out-of-order headers:", missing or "none")
    print("   missing anchors:", sorted(tpl_a - mine_a) or "none")
    print("   extra anchors:", sorted(mine_a - tpl_a) or "none")
