from __future__ import annotations

import json
import sys
from pathlib import Path
from datetime import datetime, timezone


def parse(raw: Path):
    rows = []
    cleanups = []
    for line in raw.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("CASE|"):
            _, case, status, ms, details = line.split("|", 4)
            rows.append({"case": case, "status": status, "ms": int(ms), "details": details})
        elif line.startswith("CLEANUP|"):
            cleanups.append(line)
    return rows, cleanups


def main():
    raw = Path(sys.argv[1]); out = Path(sys.argv[2])
    rows, cleanups = parse(raw)
    # Keep last result for duplicate IDs; a single final oracle per case is easier for CI.
    by_case = {}
    for row in rows:
        by_case[row["case"]] = row
    rows = [by_case[k] for k in sorted(by_case)]
    counts = {s: sum(r["status"] == s for r in rows) for s in ("PASS", "FAIL", "SKIP", "WARN")}
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": counts | {"total": len(rows)},
        "cleanup": cleanups,
        "cases": rows,
    }
    (out / "report.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    md = [
        "# Neodon VPN QA report",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        f"PASS: {counts['PASS']}  ",
        f"FAIL: {counts['FAIL']}  ",
        f"SKIP: {counts['SKIP']}  ",
        f"WARN: {counts['WARN']}  ",
        "",
        "| Case | Status | ms | Details |",
        "|---|---|---:|---|",
    ]
    for r in rows:
        md.append(f"| {r['case']} | {r['status']} | {r['ms']} | {r['details'].replace('|','\\|')} |")
    if cleanups:
        md += ["", "## Cleanup", "", *[f"- `{x}`" for x in cleanups]]
    (out / "report.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(json.dumps(payload["summary"], ensure_ascii=False))


if __name__ == "__main__":
    main()
