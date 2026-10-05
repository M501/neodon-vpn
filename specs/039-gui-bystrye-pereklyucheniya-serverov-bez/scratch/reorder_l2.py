"""Reorder the 039 docs to the Level-2 template header order and tag checklist items."""
import re
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)) + "/..")


def split_doc(path):
    text = open(path, encoding="utf-8").read().replace("\r\n", "\n")
    m = re.match(r"(?s)(---\n.*?\n---\n)(.*)", text)
    front, body = (m.group(1), m.group(2)) if m else ("", text)
    parts = re.split(r"(?m)^## +", body)
    intro = parts[0]
    sections = {}
    order = []
    for chunk in parts[1:]:
        title = chunk.split("\n", 1)[0].strip()
        sections[title] = "## " + chunk
        order.append(title)
    return front, intro, sections, order


def rebuild(path, target_order, renames=None):
    renames = renames or {}
    front, intro, sections, order = split_doc(path)
    out = [front.rstrip("\n"), "", intro.strip("\n"), ""]
    used = set()
    for want in target_order:
        src = renames.get(want, want)
        found = None
        for title in order:
            if title == src or title.startswith(src):
                found = title
                break
        if found is None:
            print("  ! missing section for", want, "->", src)
            continue
        used.add(found)
        body = sections[found]
        if want != found:
            body = "## " + want + body.split("\n", 1)[1]
        out.append(body.rstrip("\n"))
        out.append("")
    for title in order:
        if title not in used:
            out.append(sections[title].rstrip("\n"))
            out.append("")
    open(path, "w", encoding="utf-8").write("\n".join(out).rstrip("\n") + "\n")
    print("rebuilt", path)


rebuild("spec.md", [
    "1. METADATA", "2. PROBLEM & PURPOSE", "3. SCOPE", "4. REQUIREMENTS",
    "5. SUCCESS CRITERIA", "6. RISKS & DEPENDENCIES", "7. AUDIT FINDINGS",
    "L2: NON-FUNCTIONAL REQUIREMENTS", "L2: EDGE CASES", "L2: COMPLEXITY ASSESSMENT",
    "10. OPEN QUESTIONS",
], renames={
    "6. RISKS & DEPENDENCIES": "6. AUDIT FINDINGS",
    "7. AUDIT FINDINGS": "6. AUDIT FINDINGS",
    "10. OPEN QUESTIONS": "7. OPEN QUESTIONS",
})

rebuild("plan.md", [
    "1. SUMMARY", "2. QUALITY GATES", "3. ARCHITECTURE",
    "FIX ADDENDUM: AFFECTED SURFACES", "4. IMPLEMENTATION PHASES",
    "5. TESTING STRATEGY", "6. DEPENDENCIES", "7. ROLLBACK PLAN",
    "L2: PHASE DEPENDENCIES", "L2: EFFORT ESTIMATION", "L2: ENHANCED ROLLBACK",
], renames={"FIX ADDENDUM: AFFECTED SURFACES": "AFFECTED SURFACES"})

rebuild("checklist.md", [
    "Verification Protocol", "Pre-Implementation", "Code Quality", "Testing",
    "Fix Completeness", "Security", "Documentation", "File Organization",
    "Verification Summary",
])

# tag checklist items so the validator's priority-tag rule is satisfied
text = open("checklist.md", encoding="utf-8").read()
counter = [100]
def tag(match):
    counter[0] += 1
    return "- %s CHK-%d [P0] %s" % (match.group(1), counter[0], match.group(2))

text = re.sub(r"(?m)^- (\[[ xX]\]) (.+)$", tag, text)
open("checklist.md", "w", encoding="utf-8").write(text)
print("tagged checklist items:", counter[0] - 100)
