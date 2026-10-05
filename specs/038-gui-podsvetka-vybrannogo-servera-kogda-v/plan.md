---
title: "GUI: подсветка выбранного сервера + скролл только вертикальный [spec:038-gui-podsvetka-vybrannogo-servera-kogda-v]"
description: "GUI: подсветка выбранного сервера когда VPN выключен + скролл только вертикальный (тач)"
trigger_phrases:
  - "implementation"
  - "plan"
  - "name"
  - "template"
  - "plan core"
importance_tier: "normal"
contextType: "general"
_memory:
  continuity:
    packet_pointer: "specs/038-gui-podsvetka-vybrannogo-servera-kogda-v"
    last_updated_at: "2026-10-05T17:50:00Z"
    last_updated_by: "hermes-main"
    recent_action: "plan.md filled"
    next_safe_action: "Fill tasks.md then implement"
    blockers: []
    key_files: ["neodon-vpn.py", "tests/app/neodon-vpn.py"]
    session_dedup:
      fingerprint: "sha256:0d62fed10591cd75dd55ff7121bac1859a7b70ba1fb7b0250cbc5c211270aaa7"
      session_id: "main-20261005"
      parent_session_id: null
    completion_pct: 40
    open_questions: []
    answered_questions: []
---
# Implementation Plan: подсветка выбора + вертикальный скролл

<!-- SPECKIT_LEVEL: 1 -->
<!-- SPECKIT_TEMPLATE_SOURCE: plan-core | v2.2 -->

---

<!-- ANCHOR:summary -->
## 1. SUMMARY

### Technical Context

| Aspect | Value |
|--------|-------|
| **Language/Stack** | Python 3 + PySide6 6.11.2 (Qt6 Widgets) |
| **Framework** | один файл `neodon-vpn.py`, QSS-тема Fusion |
| **Storage** | `~/AI/singbox/selected-server.json` (намерение), Clash API `127.0.0.1:9090` (живая нода), `status-json` (полл бэкенда) |
| **Testing** | offscreen-проба геометрии (hRange), uinput-свайпы + grab-снимки окна, дифф изображений |

### Overview
Правка в одном файле (×2 синхронные копии): карточка сервера получает состояние «выбрано»
из `selected-server.json`, «применено» — из Clash API; горизонтальный скролл снимается
структурно — подпись карточки становится эллидящей (уходит минимальная ширина 509 px) и
скролл-область получает `_VScroll` (контент никогда не шире вьюпорта) + `ScrollBarAlwaysOff`.
<!-- /ANCHOR:summary -->

---

<!-- ANCHOR:quality-gates -->
## 2. QUALITY GATES

### Definition of Ready
- [x] Корневые причины подтверждены на устройстве (дамп конфигов, offscreen-проба ширин, синтетический свайп)
- [x] Success criteria измеримы (hRange, dx/dy, md5)
- [x] Зависимости определены (Clash API, selected-server.json)

### Definition of Done
- [ ] REQ-001..REQ-006 подтверждены пруфами
- [ ] `python3 -m py_compile` + offscreen-проба зелёные
- [ ] Живой GUI перезапущен, grab-снимки до/после сняты
- [ ] `validate.sh --strict` PASSED, CHANGES.md обновлён, коммит
<!-- /ANCHOR:quality-gates -->

---

<!-- ANCHOR:architecture -->
## 3. ARCHITECTURE

### Pattern
Однофайловое Qt-приложение (Widgets, событийный цикл + QThread-воркеры).

### Key Components
- **`selected_server()`** (новая): читает `~/AI/singbox/selected-server.json` → `{tag, server, server_port}` или `{}`.
- **`selector_now()`** (новая): Clash API `GET /proxies/proxy` → `now` вида `n<idx>` → индекс живой ноды (или `None`).
- **`refresh_active_server()`** (переписана): больше не парсит `config.json`; заполняет `selected_tag`/`selected_addr`/`active_idx`.
- **`render_servers()`** (правка): три состояния карточки (выбрана — accent-рамка, живая — зелёная рамка + `●`, обычная), подпись — `_ElidedLabel`.
- **`_select_server_idx()`** (правка): оптимистичная подсветка сразу по тапу.
- **`_status_loaded()`** (правка): смена `status.server_tag` → refresh + re-render (паритет с панелью).
- **`_VScroll`** (новый класс) + **`_page()`** (правка): вертикальный только скролл.

### Data Flow
тап → `set N` (бэкенд пишет `selected-server.json` первым) → GUI подсвечивает выбранное;
живое состояние → `status-json` полл (8 с) + Clash API для метки применённой ноды.
<!-- /ANCHOR:architecture -->

---

<!-- ANCHOR:affected-surfaces -->
## FIX ADDENDUM: AFFECTED SURFACES

| Surface | Current Role | Action | Verification |
|---------|--------------|--------|--------------|
| `MainWindow.refresh_active_server` | единственный источник `active_addr` | переписать на `selected-server.json` + Clash API | grep `active_addr` (3 места: init, refresh, select_server) + offscreen-проба |
| `MainWindow.render_servers` | рисует карточки и решает подсветку | добавить `sel`/`live`, подпись → `_ElidedLabel` | grab-снимок + проба `minimumSizeHint` |
| `MainWindow._page` / `_enable_kinetic` | создаёт скролл-области всех страниц | `_VScroll` + `ScrollBarAlwaysOff` | offscreen-проба hRange на 565/820/420 |
| `MainWindow._status_loaded` | полл `status-json` | реакция на смену `server_tag` | внешняя правка файла → grab через ≤8 с |
| `singbox-server.sh` (бэкенд) | пишет `selected-server.json` до переключения | НЕ меняем | файл уже источник истины (spec 036) |
| Decky-панель | читает тот же `selected-server.json` | НЕ меняем | общий файл = паритет |

Инвариант: подпись карточки эллизится, а не обрезается; выбор никогда не автоподключает VPN.
<!-- /ANCHOR:affected-surfaces -->

---

<!-- ANCHOR:phases -->
## 4. IMPLEMENTATION PHASES

### Phase 1: Setup
- [x] Спек-папка 038, разведка на устройстве (конфиги, ширины, синтетический тач)
- [x] Бэкап живой копии GUI перед деплоем

### Phase 2: Core Implementation
- [ ] Хелперы `selected_server()` / `selector_now()` + переписать `refresh_active_server()`
- [ ] `render_servers()`: состояния карточки + эллидящая подпись
- [ ] `_select_server_idx()`: мгновенная подсветка; `_status_loaded()`: реакция на `server_tag`
- [ ] `_VScroll` + `_page()`: вертикальный только скролл
- [ ] Синхронизировать вторую копию (`tests/app/neodon-vpn.py`) и живой файл

### Phase 3: Verification
- [ ] offscreen-проба: hRange == 0 при 565/820/420, minHint страницы home ≤ 300
- [ ] синтетические свайпы на живом окне: горизонтальные dx == 0, вертикальный dy != 0
- [ ] grab-снимки: подсветка выбранного при OFF; тап по другой карточке → подсветка переезжает
- [ ] `py_compile`, `validate.sh --strict`, CHANGES.md, коммит
<!-- /ANCHOR:phases -->

---

<!-- ANCHOR:testing -->
## 5. TESTING STRATEGY

| Test Type | Scope | Tools |
|-----------|-------|-------|
| Проба геометрии | hRange/minHint всех страниц при 3 ширинах окна | `QT_QPA_PLATFORM=offscreen` + импорт модуля GUI |
| End-to-end тач | панорамирование/скролл/тап по живому окну | uinput `hermes-test-touch` + `gui-action.json` grab + дифф изображений |
| Визуальный | подсветка выбранного/живого сервера | grab-снимки, разбор пикселей рамки |
| Регресс | бэкенд не тронут, вертикальный скролл работает | сравнение md5 конфигов, вертикальный свайп |
<!-- /ANCHOR:testing -->

---

<!-- ANCHOR:dependencies -->
## 6. DEPENDENCIES

| Dependency | Type | Status | Impact if Blocked |
|------------|------|--------|-------------------|
| `selected-server.json` | Internal | Green | нет файла → просто нет подсветки |
| Clash API `:9090` | Internal | Green (жив в 1.14) | OFF → нет метки живой ноды |
| SSH на 192.168.3.2 (LAN) | External | Green | нет деплоя/проверки — Tailscale как второй путь |
<!-- /ANCHOR:dependencies -->

---

<!-- ANCHOR:rollback -->
## 7. ROLLBACK PLAN

- **Trigger**: подсветка ломает вёрстку карточек; скролл перестаёт работать; GUI не стартует.
- **Procedure**: вернуть бэкап живой копии (`~/AI/neodon-vpn/neodon-vpn.py.pre038`), рестарт GUI;
  в репо — `git checkout -- neodon-vpn.py tests/app/neodon-vpn.py`.
<!-- /ANCHOR:rollback -->
