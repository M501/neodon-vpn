"""Rebalance the anchor pairs my earlier reorder script orphaned, and drop the bogus
parent_session_id (the validator wants a session id, not a spec folder name)."""
import os
import re

os.chdir(os.path.dirname(os.path.abspath(__file__)) + "/..")

FIXES = {
    "spec.md": [("## L2: NON-FUNCTIONAL REQUIREMENTS", "nfr"),
                ("## L2: COMPLEXITY ASSESSMENT", "complexity"),
                ("## L2: EDGE CASES", "edge-cases")],
    "plan.md": [("## L2: PHASE DEPENDENCIES", "phase-deps"),
                ("## L2: EFFORT ESTIMATION", "effort"),
                ("## L2: ENHANCED ROLLBACK", "enhanced-rollback")],
}


def rebalance(text, heading, anchor):
    lines = text.split("\n")
    # drop every anchor comment for this anchor id
    lines = [ln for ln in lines
             if not re.match(r"^\s*<!--\s*/?ANCHOR:%s\s*-->\s*$" % re.escape(anchor), ln)]
    try:
        start = next(i for i, ln in enumerate(lines) if ln.strip() == heading)
    except StopIteration:
        return text, False
    end = start + 1
    while end < len(lines) and not lines[end].startswith("## "):
        end += 1
    while end > start + 1 and lines[end - 1].strip() == "":
        end -= 1
    new = (lines[:start]
           + ["<!-- ANCHOR:%s -->" % anchor, lines[start]]
           + lines[start + 1:end]
           + ["<!-- /ANCHOR:%s -->" % anchor]
           + lines[end:])
    return "\n".join(new), True


for doc, pairs in FIXES.items():
    with open(doc, encoding="utf-8", newline="") as f:
        text = f.read().replace("\r\n", "\n")
    for heading, anchor in pairs:
        text, ok = rebalance(text, heading, anchor)
        print("%-9s %-8s %s" % (doc, anchor, "rebalanced" if ok else "HEADING NOT FOUND"))
    with open(doc, "w", encoding="utf-8", newline="") as f:
        f.write(text)

for doc in ("spec.md", "plan.md", "tasks.md", "implementation-summary.md"):
    with open(doc, encoding="utf-8", newline="") as f:
        text = f.read()
    new = re.sub(r'(?m)^(\s*parent_session_id:\s*).*$', r'\1null', text)
    if new != text:
        with open(doc, "w", encoding="utf-8", newline="") as f:
            f.write(new)
        print("parent_session_id cleared:", doc)
