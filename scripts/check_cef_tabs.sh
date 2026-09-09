#!/bin/bash
# One-shot: list CEF debugger tabs (read-only).
curl -s -m 10 http://127.0.0.1:8080/json/list 2>/dev/null | python3 -c "
import json,sys
try:
    tabs = json.load(sys.stdin)
except Exception as e:
    print('NO-TABS', e); raise SystemExit
print('TABS:', len(tabs))
for t in tabs[:12]:
    print('-', t.get('type'), '|', (t.get('title') or '')[:60], '|', (t.get('url') or '')[:80])
"
