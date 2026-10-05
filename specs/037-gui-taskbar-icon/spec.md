---
title: "NeodonVpn GUI: иконка в таскбаре KDE — привязать окно к io.neodon.gui [spec:037-gui-taskbar-icon]"
description: "В таскбаре KDE (CachyOS, Wayland) окно NeodonVpn показывается fallback-иконкой wayland (жёлтая W); фикс — setDesktopFileName(\"io.neodon.gui\") в GUI, чтобы KWin сопоставил окно с io.neodon.gui.desktop."
trigger_phrases:
  - "иконка таскбара"
  - "taskbar icon"
  - "setDesktopFileName"
  - "app_id"
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
# Feature Specification: NeodonVpn GUI — иконка в таскбаре KDE

<!-- SPECKIT_LEVEL: 1 -->
<!-- SPECKIT_TEMPLATE_SOURCE: spec-core | v2.2 -->

---

<!-- ANCHOR:metadata -->
## 1. METADATA

| Field | Value |
|-------|-------|
| **Level** | 1 |
| **Priority** | P2 |
| **Status** | In Progress |
| **Created** | 2026-10-05 |
| **Branch** | `037-gui-taskbar-icon` |
<!-- /ANCHOR:metadata -->

---

<!-- ANCHOR:problem -->
## 2. PROBLEM & PURPOSE

### Problem Statement
На портативке (Ally X, CachyOS, KDE Plasma/Wayland) в таскбаре Desktop Mode окно NeodonVpn показывается fallback-иконкой темы Breeze `wayland.svg` — «жёлтая W» — вместо иконки приложения. Диагноз доказан живьём (2026-10-05): окно несёт `desktopFileName=python3` (Qt Wayland app_id выводится из applicationName, т.к. GUI не вызывает `setDesktopFileName`); desktop-файла `python3.desktop` нет, матчинг не удаётся, и KWin рисует theme-fallback `/usr/share/icons/breeze/apps/48/wayland.svg` (градиент `#ffc35a→#faae2a`).

### Purpose
Окно (таскбар, переключатель окон, Alt-Tab) показывает ту же иконку, что на рабочем столе — `io.neodon.gui`.
<!-- /ANCHOR:problem -->

---

<!-- ANCHOR:scope -->
## 3. SCOPE

### In Scope
- Добавить `app.setDesktopFileName("io.neodon.gui")` в `main()` GUI (сразу после создания `QApplication`).
- Синхронно: live-копия на устройстве + repo-копия + `tests/app/`-копия (её берёт stage.sh) + CHANGES.md + git commit.
- Рестарт живого GUI на устройстве, верификация: KWin app_id + скриншот таскбара.

### Out of Scope
- Правка `.desktop`-файлов — не нужна: `Icon=io.neodon.gui` уже корректный, `StartupWMClass=neodon-vpn.py` остаётся как X11-легаси.
- Трей — уже использует правильную svg-иконку (`_setup_tray`, строки ~2138–2148).
- X11-сессии вне поддержки (устройство живёт на Wayland).

### Files to Change

| File Path | Change Type | Description |
|-----------|-------------|-------------|
| `/home/m26/AI/neodon-vpn/neodon-vpn.py` (live) | Modify | +1 строка в `main()`: `app.setDesktopFileName("io.neodon.gui")` |
| `C:/AI/Hermes_PROJECTS/neodon-vpn/neodon-vpn.py` (repo) | Modify | То же (md5 live == repo до правки: `ff8263cd…`) |
| `C:/AI/Hermes_PROJECTS/neodon-vpn/tests/app/neodon-vpn.py` | Modify | То же (третья синхронная копия) |
| `C:/AI/Hermes_PROJECTS/neodon-vpn/CHANGES.md` | Modify | Запись об изменении + commit (правило проекта) |
<!-- /ANCHOR:scope -->

---

<!-- ANCHOR:requirements -->
## 4. REQUIREMENTS

### P0 - Blockers (MUST complete)

| ID | Requirement | Acceptance Criteria |
|----|-------------|---------------------|
| REQ-001 | Окно GUI несёт desktop-file-name `io.neodon.gui` | KWin-скрипт на живом процессе: `KWINDBG\|…\|io.neodon.gui\|Neodon VPN\|<pid>` |
| REQ-002 | Таскбар показывает иконку приложения вместо «жёлтой W» | Скриншот панели после рестарта: на месте fallback — иконка io.neodon.gui |

### P1 - Required (complete OR user-approved deferral)

| ID | Requirement | Acceptance Criteria |
|----|-------------|---------------------|
| REQ-003 | Все три копии кода синхронны | md5(live) == md5(repo) == md5(tests/app) после деплоя |
| REQ-004 | Нет регрессии запуска: single-instance/хук/трей работают | GUI стартует, окно открывается, `gui-action.json`-хук отрабатывает |
<!-- /ANCHOR:requirements -->

---

<!-- ANCHOR:success-criteria -->
## 5. SUCCESS CRITERIA

- **SC-001**: KWin видит окно NeodonVPN с `desktopFileName=io.neodon.gui` (было `python3`).
- **SC-002**: на скриншоте таскбара вместо жёлтой W — иконка `io.neodon.gui` (пруф до/после).
- **SC-003**: CHANGES.md + commit в репо содержат правку; live деплой подтверждён md5.
<!-- /ANCHOR:success-criteria -->

---

<!-- ANCHOR:risks -->
## 6. RISKS & DEPENDENCIES

| Type | Item | Impact | Mitigation |
|------|------|--------|------------|
| Dependency | KWin сопоставляет native-Wayland app_id с `<app_id>.desktop` | Без матчинга фикс не сработает | Механика подтверждена живьём: `org.kde.konsole` резолвится в свою иконку; `io.neodon.gui.desktop` лежит в `~/.local/share/applications/` |
| Risk | `setDesktopFileName` влияет и на X11 WM_CLASS | Low — устройство на Wayland, `.desktop` несёт StartupWMClass | Откат = revert одной строки; X11 не в скоупе |
| Risk | Живой процесс держит старый код | Верификация покажет старый app_id | Рестарт GUI обязателен до верификации |
<!-- /ANCHOR:risks -->

---

<!-- ANCHOR:questions -->
## 7. OPEN QUESTIONS

- Нет: причина и фикс доказаны эмпирически (KWINDBG + wayland.svg + скрин) и по докам Qt.
<!-- /ANCHOR:questions -->

---

## Research (2026-10-05)

- Qt 6 docs, `QGuiApplication::desktopFileName`: «gives a precise indication of what desktop entry represents the application and it is needed by the windowing system to retrieve such information without resorting to imprecise heuristics» — https://doc.qt.io/qt-6/qguiapplication.html#desktopFileName-prop (проверено web_extract, doc Qt 6.12).
- Живые доказательства (device, Desktop Mode): `KWINDBG|python3|python3.14|python3|Neodon VPN|15775` — app_id окна = `python3`; fallback-иконка = `/usr/share/icons/breeze/apps/48/wayland.svg` («жёлтая W»); `~/.local/share/applications/io.neodon.gui.desktop` несёт `Icon=io.neodon.gui`.
- Примечание: внешний web_search в момент работы деградировал (шумная выдача) — опора на первичный источник (Qt doc) + живые замеры.

---

<!--
CORE TEMPLATE (~80 lines)
- Essential what/why/how only
- No boilerplate sections
- Add L2/L3 addendums for complexity
-->