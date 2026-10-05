"""Rebuild every anchor pair from the templates: strip all anchor comments, then wrap
each section whose heading the template pairs with an anchor. Deterministic, so nesting
cannot end up shuffled (which is what the validator rejected)."""
import os
import re

os.chdir(os.path.dirname(os.path.abspath(__file__)) + "/..")

OPEN = re.compile(r"^\s*<!--\s*ANCHOR:([a-z0-9-]+)\s*-->\s*$")
CLOSE = re.compile(r"^\s*<!--\s*/ANCHOR:[a-z0-9-]+\s*-->\s*$")
DOCS = ["spec.md", "plan.md", "tasks.md", "implementation-summary.md"]


def template_map(path):
    """heading -> anchor id, taken from the template's own section order."""
    if not os.path.exists(path):
        return {}
    pending, out = None, {}
    for line in open(path, encoding="utf-8", errors="replace", newline="").read().replace("\r\n", "\n").split("\n"):
        mo = OPEN.match(line)
        if mo:
            pending = mo.group(1)
            continue
        if line.startswith("## ") and pending:
            out[line.strip()] = pending
            pending = None
    return out


for doc in DOCS:
    tmap = template_map(os.path.join("scratch", doc))
    if not tmap:
        print("%-26s no template map, skipped" % doc)
        continue
    lines = [ln for ln in open(doc, encoding="utf-8", newline="").read().replace("\r\n", "\n").split("\n")
             if not OPEN.match(ln) and not CLOSE.match(ln)]
    out, used = [], []
    i = 0
    while i < len(lines):
        line = lines[i]
        anchor = tmap.get(line.strip())
        if anchor and line.startswith("## "):
            end = i + 1
            while end < len(lines) and not lines[end].startswith("## "):
                end += 1
            while end > i + 1 and lines[end - 1].strip() == "":
                end -= 1
            out.append("<!-- ANCHOR:%s -->" % anchor)
            out.extend(lines[i:end])
            out.append("<!-- /ANCHOR:%s -->" % anchor)
            used.append(anchor)
            i = end
            continue
        out.append(line)
        i += 1
    with open(doc, "w", encoding="utf-8", newline="") as f:
        f.write("\n".join(out))
    missing = [a for a in tmap.values() if a not in used]
    print("%-26s anchors written: %d, missing from doc: %s" % (doc, len(used), missing or "none"))
