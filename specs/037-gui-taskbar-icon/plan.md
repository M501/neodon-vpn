---
title: "NeodonVpn GUI: иконка в таскбаре KDE — привяза [spec:037-gui-taskbar-icon]"
description: "План точечного фикса: setDesktopFileName(\"io.neodon.gui\") в main() GUI; синхрон трёх копий (live/repo/tests), рестарт, верификация KWin app_id + скриншот."
trigger_phrases:
  - "implementation"
  - "plan"
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
# Implementation Plan: NeodonVpn GUI — иконка в таскбаре KDE

<!-- SPECKIT_LEVEL: 1 -->
<!-- SPECKIT_TEMPLATE_SOURCE: plan-core | v2.2 -->

---

<!-- ANCHOR:summary -->
## 1. SUMMARY

### Technical Context

| Aspect | Value |
|--------|-------|
| **Language/Stack** | Python 3.14 + PySide6 6.11.2 (Qt 6, Wayland) |
| **Framework** | KDE Plasma 6 / KWin (Wayland), CachyOS на Ally X |
| **Storage** | — |
| **Testing** | Живой прогон: KWin-script (D-Bus) + spectacle-скриншот + md5-сверка |

### Overview
Одна строка `app.setDesktopFileName("io.neodon.gui")` в `main()` связывает Wayland-окно с `io.neodon.gui.desktop`, после чего KWin берёт Name/Icon из desktop-файла. Правка синхронно ложится в 3 копии (live, repo, tests/app), затем рестарт живого GUI и двойная верификация: app_id в KWin + пиксельный пруф скриншотом до/после.
<!-- /ANCHOR:summary -->

---

<!-- ANCHOR:quality-gates -->
## 2. QUALITY GATES

### Definition of Ready
- [x] Problem statement clear and scope documented
- [x] Success criteria measurable
- [x] Dependencies identified (KWin app_id-matching подтверждён живьём)

### Definition of Done
- [ ] All acceptance criteria met
- [ ] Tests passing (if applicable)
- [ ] Docs updated (spec/plan/tasks)
<!-- /ANCHOR:quality-gates -->

---

<!-- ANCHOR:architecture -->
## 3. ARCHITECTURE

### Pattern
Точечный багфикс в существующем GUI (без новых компонентов).

### Key Components
- **GUI (`neodon-vpn.py`)**: единственное место правки — `main()` сразу после `app = QApplication(sys.argv)`.
- **.desktop (`io.neodon.gui.desktop`)**: уже корректный (`Icon=io.neodon.gui`), не меняется.
- **KWin**: сопоставляет app_id окна с именем desktop-файла и подтягивает иконку.

### Data Flow
`QApplication` создаётся → `setDesktopFileName("io.neodon.gui")` → Wayland `xdg_toplevel.set_app_id` = `io.neodon.gui` → KWin находит `~/.local/share/applications/io.neodon.gui.desktop` → иконка `io.neodon.gui` у всех потребителей (таскбар, переключатель, Alt-Tab).
<!-- /ANCHOR:architecture -->

---

<!-- ANCHOR:affected-surfaces -->
## FIX ADDENDUM: AFFECTED SURFACES

Use this section when `research_intent=fix_bug`, when planning from a deep-review FAIL/CONDITIONAL verdict, or when any finding touches security, path handling, env precedence, schema boundaries, persistence, public responses, or shared policy.

| Surface | Current Role | Action | Verification |
|---------|--------------|--------|--------------|
| `neodon-vpn.py` `main()` | producer: создаёт QApplication/окно | update (+1 строка) | `grep -n setDesktopFileName` по 3 копиям |
| live-процесс GUI на устройстве | consumer: несёт app_id окна | restart обязателен | `KWINDBG` строка: `io.neodon.gui` |
| `.desktop`-файлы (menu/Desktop/autostart) | consumer: иконка для DE | unchanged | `Icon=io.neodon.gui` уже корректен |
| трей (`_setup_tray`) | independent: отдельная иконка из svg | unchanged | код уже использует `io.neodon.gui.svg` |

Required inventories:
- Same-class producers: `grep -n "QApplication(sys.argv)\|setDesktopFileName\|setApplicationName" neodon-vpn.py` — единственный producer `main()`; `setApplicationName` отсутствует.
- Consumers changed symbol: `grep -rn "io.neodon.gui"` (lock-путь `~/.var/app/io.neodon.gui`, пути иконок, .desktop) — строковое совпадение, менять ничего не требуется.
- Matrix axes: сессия (Wayland — проверяем; X11 — вне скоупа), потребители (таскбар/переключатель/Alt-Tab — один механизм KWin).
- Algorithm invariant: app_id окна == basename `~/.local/share/applications/io.neodon.gui.desktop` (без `.desktop`); adversarial-случай — чужой app_id (`python3`) = fallback wayland.svg (воспроизведён живьём).
<!-- /ANCHOR:affected-surfaces -->

---

<!-- ANCHOR:phases -->
## 4. IMPLEMENTATION PHASES

### Phase 1: Setup
- [x] Спек-папка 037 создана (spec-new, validate PASSED)
- [x] Research: Qt doc + живой диагноз (KWINDBG app_id=python3, wayland.svg, скрин «до»)

### Phase 2: Core Implementation
- [ ] Правка `neodon-vpn.py` (repo корень): +1 строка в `main()`
- [ ] Синхронизация `tests/app/neodon-vpn.py`
- [ ] Деплой live через SFTP + md5-сверка трёх копий
- [ ] CHANGES.md + git commit

### Phase 3: Verification
- [ ] Рестарт живого GUI (kill + systemd-run, переживает SSH)
- [ ] `KWINDBG` → `desktopFileName=io.neodon.gui`
- [ ] Скриншот таскбара → иконка вместо «жёлтой W»
- [ ] validate.sh --strict + обновление спек-доков
<!-- /ANCHOR:phases -->

---

<!-- ANCHOR:testing -->
## 5. TESTING STRATEGY

| Test Type | Scope | Tools |
|-----------|-------|-------|
| Smoke | GUI стартует после рестарта, single-instance не ломается | `ps`, flock-поведение |
| Integration | KWin сопоставляет окно с desktop-файлом | KWin-script (`loadScript`/`start`) + `journalctl` grep KWINDBG |
| Manual (visual) | Иконка в таскбаре на скриншоте | `spectacle -b -f -n` + vision-кроп панели |
<!-- /ANCHOR:testing -->

---

<!-- ANCHOR:dependencies -->
## 6. DEPENDENCIES

| Dependency | Type | Status | Impact if Blocked |
|------------|------|--------|-------------------|
| KWin Wayland app_id→desktop matching | External | Green (подтверждён живьём) | Фикс не даст эффекта |
| `io.neodon.gui.desktop` + svg в `~/.local/share/...` | Internal | Green (файлы на месте) | Останется fallback |
| SSH/put_file/SFTP до устройства | Internal | Green | Нет деплоя/верификации |
<!-- /ANCHOR:dependencies -->

---

<!-- ANCHOR:rollback -->
## 7. ROLLBACK PLAN

- **Trigger**: GUI не стартует после правки, или иконка/поведение сломались.
- **Procedure**: revert одной строки `setDesktopFileName` во всех трёх копиях (md5 до правки `ff8263cd881a9d0b665dcb91c8f1d316`), повторный деплой live + рестарт GUI.
<!-- /ANCHOR:rollback -->

---

<!--
CORE TEMPLATE (~90 lines)
- Essential technical planning
- Simple phase structure
- Add L2/L3 addendums for complexity
-->