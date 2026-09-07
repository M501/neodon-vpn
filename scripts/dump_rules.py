#!/usr/bin/env python3
"""One-shot: dump smart route.rules shape (spec 007)."""
import json

d = json.load(open("/home/m26/AI/singbox/config.json"))
rules = d["route"]["rules"]
print("RULES:", len(rules))
for r in rules[:16]:
    print(json.dumps(r, ensure_ascii=False)[:220])
print("FINAL:", d["route"].get("final"))
print("RULE_SETS:", json.dumps(d["route"].get("rule_set", []), ensure_ascii=False)[:300])
