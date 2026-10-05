---
title: "Neodon панель Decky: отзывчивое переключени [spec:035-panel-switch-ux]"
description: "Neodon панель Decky: отзывчивое переключение сервера и понятные статусы — мгновенный switching-индикатор, человеческие тексты вместо сырых FAILED/urlopen, ретрай повторного тапа по серверу, TTL transition-маркера 12с, ранняя запись selected-server.json"
trigger_phrases:
  - "tasks"
  - "name"
  - "template"
  - "tasks core"
importance_tier: "normal"
contextType: "general"
_memory:
  continuity:
    packet_pointer: "specs/035-panel-switch-ux"
    last_updated_at: "2026-10-04T00:52:38Z"
    last_updated_by: "hermes-main"
    recent_action: "Spec folder created"
    next_safe_action: "Fill spec.md"
    blockers: []
    key_files: []
    session_dedup:
      fingerprint: "sha256:66fe3c95194e019c99a60246f874f5ec63dae6209757940e62ccf55a49e2e7f7"
      session_id: "main-20261004"
      parent_session_id: null
    completion_pct: 0
    open_questions: []
    answered_questions: []
---
# Tasks: Panel switch UX

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

- [x] T001 Спека 035 создана и заполнена (specs/035-panel-switch-ux)
- [x] T002 [P] Диагноз по журналам + md5-база сняты; скан 12 серверов (живые 0,1,3,5,7,8,9)
- [x] T003 Бэкапы целевых файлов на устройстве (deploy_prep.sh: toggle/server/dist-js + .bak-20261004-ux; dist/index.js.map на устройстве до заливки отсутствовал)
<!-- /ANCHOR:phase-1 -->

---

<!-- ANCHOR:phase-2 -->
## Phase 2: Implementation

- [x] T004 index.tsx: pendRef + notice + shortErr + FRIENDLY + подсказка DEGRADED/FAILED (decky/neodon-vpn/src/index.tsx)
- [x] T005 index.tsx: ретрай-тап по тому же серверу при не-CONNECTED; эхо-окно 0.8 с (decky/neodon-vpn/src/index.tsx)
- [x] T006 index.tsx: pending-оверрайд строки статуса; снятие по подтверждению/15 с; сброс при ok=false (decky/neodon-vpn/src/index.tsx)
- [x] T007 rollup build: dist/index.js + map (decky/neodon-vpn)
- [x] T008 singbox-toggle.sh: TTL маркера 30→12 с (scripts/singbox-toggle.sh)
- [x] T009 singbox-server.sh: selected-server.json до рестарта, после успешного check (scripts/singbox-server.sh)
- [x] T010 Синк корневых репо-копий (singbox-toggle.sh, singbox-server.sh в корне репо)
<!-- /ANCHOR:phase-2 -->

---

<!-- ANCHOR:phase-3 -->
## Phase 3: Verification

- [x] T011 Живой прогон: set_server на живой (0/PL) — замер, CONNECTED, магазин 200
- [x] T012 Живой прогон: set_server на мёртвый (4/DE) — TRANSITIONING ≤12 с → DEGRADED; повторный тап = повторный set_server (бэкенд подтверждён; пары тапов — на приёмке)
- [x] T013 journal plugin_loader: без фантомов/пинг-понга в прогоне; backend up
- [x] T014 CHANGES.md (60) + validate.sh --strict + git commit f920768 + push via API (a6ce997)
- [x] T015 Питфолы в скилл bazzite-neodon-vpn (TTL, ретрай-тап, friendly-маппинг, early persist)
- [ ] T016 Приёмка владельцем по его сценарию (панель: смена, повторный тап, Refresh)
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
