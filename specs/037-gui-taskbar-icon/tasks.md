---
title: "NeodonVpn GUI: иконка в таскбаре KDE — привяза [spec:037-gui-taskbar-icon]"
description: "Чеклист фикса: диагноз доказан; остаётся правка 3 копий, деплой live, рестарт GUI и верификация (KWINDBG + скриншот)."
trigger_phrases:
  - "tasks"
  - "setDesktopFileName"
  - "taskbar icon"
importance_tier: "normal"
contextType: "general"
_memory:
  continuity:
    packet_pointer: "specs/037-gui-taskbar-icon"
    last_updated_at: "2026-10-05T02:27:16Z"
    last_updated_by: "hermes-main"
    recent_action: "Spec folder created"
    next_safe_action: "Fill spec.md"
    blockers: []
    key_files: []
    session_dedup:
      fingerprint: "sha256:2e547ada75cd63804b9d043483d981bc2d68adc599538ce4ee35a74e43730ab2"
      session_id: "main-20261005"
      parent_session_id: null
    completion_pct: 0
    open_questions: []
    answered_questions: []
---
# Tasks: NeodonVpn GUI — иконка в таскбаре KDE

<!-- SPECKIT_LEVEL: 1 -->
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

- [x] T001 Создать спек-папку 037 (spec-new, validate PASSED)
- [x] T002 [P] Живой диагноз: KWINDBG app_id=python3, fallback wayland.svg, скрин «до»
- [x] T003 Research: Qt doc desktopFileName (первичный источник) — записан в spec.md
<!-- /ANCHOR:phase-1 -->

---

<!-- ANCHOR:phase-2 -->
## Phase 2: Implementation

- [x] T004 Правка `main()`: `app.setDesktopFileName("io.neodon.gui")` (neodon-vpn.py, корень repo)
- [x] T005 [P] Синхронизировать tests/app/neodon-vpn.py
- [x] T006 Деплой live SFTP + md5-сверка всех трёх копий (md5 `3d5938ce…` ×3)
- [x] T007 CHANGES.md: запись (2026-10-05 (66))
- [x] T012 git commit + push в GitHub — выполнено параллельным reconcile-процессом: merge `82c8d58`, CHANGES+tasks `8e8dd1b`, summary+spec `f4a5bff` (origin/master = `f4a5bff`)
<!-- /ANCHOR:phase-2 -->

---

<!-- ANCHOR:phase-3 -->
## Phase 3: Verification

- [x] T008 Рестарт живого GUI (kill + systemd-run --user, переживает SSH)
- [x] T009 KWINDBG-прогон: desktopFileName == io.neodon.gui (REQ-001/SC-001)
- [x] T010 Скриншот таскбара: иконка вместо жёлтой W (REQ-002/SC-002)
- [x] T011 validate.sh --strict + итоговый md5 (REQ-003/SC-003)
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