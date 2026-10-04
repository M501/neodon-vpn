---
title: "Selector instant switch [spec:036-selector-instant-switch]"
description: "Mini phase 1: selector + urltest + Clash API — мгновенное переключение сервера без рестарта"
trigger_phrases:
  - "tasks"
importance_tier: "normal"
contextType: "general"
_memory:
  continuity:
    packet_pointer: "specs/036-selector-instant-switch"
    last_updated_at: "2026-10-04T06:00:00Z"
    last_updated_by: "hermes-main"
    recent_action: "Tasks filled"
    next_safe_action: "Owner acceptance"
    blockers: []
    key_files: []
    session_dedup:
      fingerprint: "sha256:66fe3c95194e019c99a60246f874f5ec63dae6209757940e62ccf55a49e2e7f7"
      session_id: "main-20261004"
      parent_session_id: null
    completion_pct: 95
    open_questions: []
    answered_questions: []
---
# Tasks: Selector instant switch

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

- [x] T001 Факт-чек доков sing-box 1.14 (selector/urltest/Clash API/cache_file)
- [x] T002 Бэкап-план: конфиги .pre-sel-20261004, скрипты .bak-20261004-sel
<!-- /ANCHOR:phase-1 -->

---

<!-- ANCHOR:phase-2 -->
## Phase 2: Implementation

- [x] T003 migrate_selector.py: 12 нод + urltest auto + selector(proxy) + clash_api + cache_file (3 конфига)
- [x] T004 scripts/singbox-server.sh: rewrite на PUT + персист + фоллбэки
- [x] T005 scripts/singbox-toggle.sh: apply_pref в smart/full/proxy
- [x] T006 killswitch.sh: allowlist всех влess-нод (FULL)
- [x] T007 Панель: key-ремаунт дропдауна серверов + rebuild dist
<!-- /ANCHOR:phase-2 -->

---

<!-- ANCHOR:phase-3 -->
## Phase 3: Verification

- [x] T008 sing-box check ×3 PASS; миграция атомарная
- [x] T009 Живой прогон: OFF→smart→CONNECTED 4 с (apply_pref n0)
- [x] T010 set 1 = 0.10 с (exit NL 203.188.180.46); set 0 = 0.09 с (exit PL 94.183.209.102)
- [x] T011 Clash API GET /proxies/proxy: now=nN, all=[n0..n11,auto]
- [x] T012 md5 синк; plugin_loader рестарт; backend up
- [x] T013 CHANGES.md (64) + commit + push
- [ ] T014 Приёмка владельца: смена сервера из QAM (мгновенно), магазин
<!-- /ANCHOR:phase-3 -->

---

<!-- ANCHOR:completion -->
## Completion Criteria

- [ ] All tasks marked `[x]`
- [x] No `[B]` blocked tasks remaining
- [ ] Manual verification passed (владелец)
<!-- /ANCHOR:completion -->

---

<!-- ANCHOR:cross-refs -->
## Cross-References

- **Specification**: See `spec.md`
- **Plan**: See `plan.md`
<!-- /ANCHOR:cross-refs -->
