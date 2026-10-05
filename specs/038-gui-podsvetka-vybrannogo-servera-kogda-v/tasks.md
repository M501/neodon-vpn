---
title: "GUI: подсветка выбранного сервера + скролл только вертикальный [spec:038-gui-podsvetka-vybrannogo-servera-kogda-v]"
description: "GUI: подсветка выбранного сервера когда VPN выключен + скролл только вертикальный (тач)"
trigger_phrases:
  - "tasks"
  - "name"
  - "template"
  - "tasks core"
importance_tier: "normal"
contextType: "general"
_memory:
  continuity:
    packet_pointer: "specs/038-gui-podsvetka-vybrannogo-servera-kogda-v"
    last_updated_at: "2026-10-05T17:50:00Z"
    last_updated_by: "hermes-main"
    recent_action: "tasks.md filled"
    next_safe_action: "commit + push"
    blockers: []
    key_files: ["neodon-vpn.py", "tests/app/neodon-vpn.py"]
    session_dedup:
      fingerprint: "sha256:0d62fed10591cd75dd55ff7121bac1859a7b70ba1fb7b0250cbc5c211270aaa7"
      session_id: "main-20261005"
      parent_session_id: null
    completion_pct: 100
    open_questions: []
    answered_questions: []
---
# Tasks: подсветка выбора + вертикальный скролл

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

- [x] T001 Создать спек-папку 038, зафиксировать жалобу владельца в spec.md (`specs/038-.../spec.md`)
- [x] T002 Снять пруфы причин: дамп `proxy`-аутбаунда (selector, без `server`) во всех трёх конфигах, offscreen-проба ширин, синтетический свайп (`specs/_scratch_*.py|sh`, `probe.json`)
- [x] T003 Бэкап живой копии GUI перед деплоем (`~/AI/neodon-vpn/neodon-vpn.py.pre038`)
<!-- /ANCHOR:phase-1 -->

---

<!-- ANCHOR:phase-2 -->
## Phase 2: Implementation

- [x] T004 Хелпер `selected_server()` + `selector_now()`, переписать `refresh_active_server()` (`neodon-vpn.py`)
- [x] T005 `render_servers()`: состояния «выбрана/живая/обычная» + эллидящая подпись (`neodon-vpn.py`)
- [x] T006 `_select_server_idx()` мгновенная подсветка; `_status_loaded()` реакция на `server_tag` (`neodon-vpn.py`)
- [x] T007 `_VScroll` + `_page()`: `ScrollBarAlwaysOff` и кламп ширины контента (`neodon-vpn.py`)
- [x] T008 Синхронизировать `tests/app/neodon-vpn.py` и запушить на устройство
<!-- /ANCHOR:phase-2 -->

---

<!-- ANCHOR:phase-3 -->
## Phase 3: Verification

- [x] T009 offscreen-проба: `hRange == 0` при 565/820/420 и `minHint(home) < 300` (устройство)
- [x] T010 Синтетические свайпы на живом окне: горизонтальные `dx == 0` (обе стороны), вертикальный `dy != 0`
- [x] T011 grab-снимки: подсветка выбранного при OFF; тап по другой карточке → подсветка + `selected-server.json` совпадают
- [x] T012 `py_compile` обеих копий, `validate.sh --strict`, CHANGES.md, коммит + пуш
<!-- /ANCHOR:phase-3 -->

---

<!-- ANCHOR:completion -->
## Completion Criteria

- [x] All tasks marked `[x]`
- [x] No `[B]` blocked tasks remaining
- [x] Manual verification passed (grab-снимки + синтетический палец, см. implementation-summary.md)
<!-- /ANCHOR:completion -->

---

<!-- ANCHOR:cross-refs -->
## Cross-References

- **Specification**: See `spec.md`
- **Plan**: See `plan.md`
<!-- /ANCHOR:cross-refs -->
