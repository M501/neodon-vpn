---
title: "VPN status hardening: bounded probes + intent switch [spec:034-vpn-status-hardening]"
description: "VPN status hardening: bounded probes + intent switch"
trigger_phrases:
  - "tasks"
  - "name"
  - "template"
  - "tasks core"
importance_tier: "normal"
contextType: "general"
_memory:
  continuity:
    packet_pointer: "specs/034-vpn-status-hardening"
    last_updated_at: "2026-10-03T22:10:00Z"
    last_updated_by: "hermes-main"
    recent_action: "Implemented + verified live (034)"
    next_safe_action: "None - complete"
    blockers: []
    key_files: []
    session_dedup:
      fingerprint: "sha256:f8c35e8af966969c48ef6983eddc4e408af39d552e36b07983976284f4d32186"
      session_id: "main-20261003"
      parent_session_id: null
    completion_pct: 100
    open_questions: []
    answered_questions: []
---
# Tasks: VPN status hardening — bounded probes + intent switch

<!-- SPECKIT_LEVEL: 2 -->
<!-- SPECKIT_TEMPLATE_SOURCE: tasks-core | v2.2 -->

---

<!-- ANCHOR:notation -->
## Task Notation

| Prefix | Meaning |
|--------|---------|
| `[ ]` | Pending |
| `[x]` | Completed |
| `[P]` | Parallelizable |
| `[B]` | Blocked |

**Task Format**: `T### [P?] Description (file path)`
<!-- /ANCHOR:notation -->

---

<!-- ANCHOR:phase-1 -->
## Phase 1: Setup

- [x] T001 Бэкапы live-файлов на устройстве (.bak-20261004)
- [x] T002 LF-нормализация редактируемых файлов
- [x] T003 [P] Baseline-замеры (healthy 0.5 с / dead >40 с)
<!-- /ANCHOR:phase-1 -->

---

<!-- ANCHOR:phase-2 -->
## Phase 2: Implementation

- [x] T004 Bounds (timeout) всех внешних проб status-json (scripts/singbox-toggle.sh)
- [x] T005 get_status timeout 15→30 (decky/neodon-vpn/main.py)
- [x] T006 Switch=intent + timer guard (decky/neodon-vpn/src/index.tsx)
- [x] T007 Пересборка dist/index.js (rollup)
- [x] T008 Деплой на устройство + рестарт plugin_loader
- [x] T009 Сервер #0 PL + репо-синк (root toggle/server, watchdog, heal)
- [x] T014 Пикер: domain_resolver bootstrap + config-proxy.json + маркер перед рестартами (scripts/singbox-server.sh)
- [x] T015 heal restart-guard (маркер + auto-restart) + порядок heal→маркер в toggle
<!-- /ANCHOR:phase-2 -->

---

<!-- ANCHOR:phase-3 -->
## Phase 3: Verification

- [x] T010 Живой цикл: off→smart→CONNECTED→off (exit PL)
- [x] T011 Dead-server: bounded статус ≤20 с (было >40 с), без шторма
- [x] T012 CHANGES.md + git commit + push (GitHub API)
- [x] T013 Пруфы в spec/checklist, validate.sh --strict зелёный
- [x] T016 Switch-верификация: NL/PL живьём, `.mode` стабилен, без heal-флапов
<!-- /ANCHOR:phase-3 -->

---

<!-- ANCHOR:completion -->
## Completion Criteria

- [ ] All tasks marked `[x]`
- [ ] No `[B]` blocked tasks remaining
- [ ] Manual verification passed
<!-- /ANCHOR:completion -->

---

<!-- ANCHOR:cross-refs -->
## Cross-References

- **Specification**: See `spec.md`
- **Plan**: See `plan.md`
<!-- /ANCHOR:cross-refs -->

---

<!--
CORE TEMPLATE (~60 lines)
- Simple task tracking
- 3 phases: Setup, Implementation, Verification
- Add L2/L3 addendums for complexity
-->