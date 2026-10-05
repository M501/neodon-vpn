---
title: "Задачи 039: быстрые переключения, флаги, аудит [spec:039-gui-bystrye-pereklyucheniya-serverov-bez]"
description: "GUI: быстрые переключения серверов без прыжков подсветки, немецкий флаг, аудит и доводка до продакшена"
trigger_phrases:
  - "tasks"
  - "fast switching"
  - "audit"
importance_tier: "normal"
contextType: "general"
_memory:
  continuity:
    packet_pointer: "specs/039-gui-bystrye-pereklyucheniya-serverov-bez"
    last_updated_at: "2026-10-05T21:50:00Z"
    last_updated_by: "hermes-main"
    recent_action: "tasks.md filled"
    next_safe_action: "acceptance run + commit"
    blockers: []
    key_files: ["neodon-vpn.py", "flags/DE.png"]
    session_dedup:
      fingerprint: "sha256:0d62fed10591cd75dd55ff7121bac1859a7b70ba1fb7b0250cbc5c211270aaa7"
      session_id: "main-20261005"
      parent_session_id: "038-gui-podsvetka-vybrannogo-servera-kogda-v"
    completion_pct: 85
    open_questions: []
    answered_questions: []
---
# Tasks: быстрые переключения, флаги, аудит

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
## Phase 1: Диагностика

- [x] T101 Дамп `proxy`-аутбаунда и `selected-server.json`; подтверждение, что выбор живёт только в файле (`neodon-vpn.py`)
- [x] T102 Воспроизведение прыжков: два быстрых тапа + бурст снимков окна (`scratch/scripts/_scratch_flicker.sh`)
- [x] T103 Спай событий Qt: нажатие второго быстрого тапа уходит в QWindow (`scratch/neodon-vpn-dbg.py` + `_scratch_spy.sh`)
- [x] T104 Замер гэпов 150/500/1000/2000 мс: потеря нажатия только до ~0.5 с (`_scratch_tap2_gaps.sh`)
- [x] T105 Проверка набора флагов: репо = `flagcdn.com/w40/*.png`, `DE.png` отсутствует (`_scratch_flagcheck.py`)
- [x] T106 Запрошены три независимых read-only аудита (GUI, control-plane, Decky)
<!-- /ANCHOR:phase-1 -->

---

<!-- ANCHOR:phase-2 -->
## Phase 2: Правки

- [x] T107 Интент выбора + settle-окно вместо трёх равноправных писателей (`neodon-vpn.py`)
- [x] T108 `_paint_selection()` — перерисовка выбора на месте, сетка не пересобирается (`neodon-vpn.py`)
- [x] T109 Обработка `mouseDoubleClickEvent` + ограниченный «отпуск без нажатия» (окно 0.6 с, неподвижный скролл) (`neodon-vpn.py`)
- [x] T110 `flags/DE.png` (flagcdn w40, как остальные) + фолбэк «код страны» (`flags/DE.png`, `neodon-vpn.py`)
- [x] T111 Аудит-фиксы по трём отчётам (`neodon-vpn.py` / скрипты / Decky) — по мере поступления
<!-- /ANCHOR:phase-2 -->

---

<!-- ANCHOR:phase-3 -->
## Phase 3: Проверка

- [ ] T112 Приёмочный прогон: тапы 150/250 мс, одиночный тап, overscroll, вертикальный и горизонтальный свайпы, внешний `set` (`_scratch_verify039c.sh`)
- [x] T113 Бэкап живой копии `.pre039` + рестарт GUI на новом билде
- [x] T114 Сверка md5 (live = repo = tests/app), `py_compile`, offscreen-проба `hRange = 0`
- [ ] T115 `validate.sh --strict`, CHANGES.md (запись 68), коммит в GitHub
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
- **Предшествующая волна**: `specs/038-gui-podsvetka-vybrannogo-servera-kogda-v`
<!-- /ANCHOR:cross-refs -->
