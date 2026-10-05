---
title: "План 039: быстрые переключения без прыжков, флаги, аудит [spec:039-gui-bystrye-pereklyucheniya-serverov-bez]"
description: "GUI: быстрые переключения серверов без прыжков подсветки, немецкий флаг, аудит и доводка до продакшена"
trigger_phrases:
  - "implementation"
  - "plan"
  - "fast switching"
  - "audit"
importance_tier: "normal"
contextType: "general"
_memory:
  continuity:
    packet_pointer: "specs/039-gui-bystrye-pereklyucheniya-serverov-bez"
    last_updated_at: "2026-10-05T21:45:00Z"
    last_updated_by: "hermes-main"
    recent_action: "plan.md filled"
    next_safe_action: "tasks.md + implementation of audit fixes"
    blockers: []
    key_files: ["neodon-vpn.py", "flags/DE.png"]
    session_dedup:
      fingerprint: "sha256:0d62fed10591cd75dd55ff7121bac1859a7b70ba1fb7b0250cbc5c211270aaa7"
      session_id: "main-20261005"
      parent_session_id: "038-gui-podsvetka-vybrannogo-servera-kogda-v"
    completion_pct: 50
    open_questions: []
    answered_questions: []
---

# Implementation Plan: быстрые переключения, флаги, доводка

<!-- SPECKIT_LEVEL: 1 -->
<!-- SPECKIT_TEMPLATE_SOURCE: plan-core | v2.2 -->

---

<!-- ANCHOR:summary -->

## 1. SUMMARY

### Technical Context

| Aspect | Value |
|--------|-------|
| **Language/Stack** | Python 3 + PySide6 6.11.2 (Qt6 Widgets, один файл) |
| **Storage** | `~/AI/singbox/selected-server.json` (выбор), Clash API `127.0.0.1:9090` (живая нода), `status-json` (полл) |
| **Testing** | синтетический тач (uinput) + снимки окна хуком приложения + разбор пикселей; offscreen-проба геометрии |

### Overview
Единый владелец состояния выбора (интент пользователя), перерисовка подсветки на месте без пересборки
сетки карточек, корректная обработка второго быстрого тапа (Qt отдаёт его нажатие в QWindow), флаг DE
из того же набора, что и остальные, и закрытие подтверждённых аудитом дефектов.
<!-- /ANCHOR:summary -->

---

<!-- ANCHOR:quality-gates -->

## 2. QUALITY GATES

### Definition of Ready
- [x] Все три корневые причины измерены на устройстве (лог карточек, спай событий, дамп конфигов/флагов)
- [x] Критерии приёмки проверяемы (файл выбора + пиксели рамки/флага)
- [x] Отчёты трёх ревьюеров запрошены

### Definition of Done
- [ ] REQ-101..REQ-108 подтверждены
- [ ] `py_compile` обеих копий; offscreen-проба геометрии зелёная
- [ ] Живой GUI перезапущен на новом билде, снимки до/после сняты
- [ ] `validate.sh --strict` PASSED, CHANGES.md, коммит и пуш
<!-- /ANCHOR:quality-gates -->

---

<!-- ANCHOR:architecture -->

## 3. ARCHITECTURE

### Pattern
Однофайловое Qt-приложение: страницы + воркеры (QThread) + бэкенд через `subprocess`.

### Key Components
- **Интент выбора** `_sel_intent` + окно `_sel_settle_until`: пока выбор не подтверждён, файл и полл НЕ перебивают подсветку.
- **`_paint_selection()`**: единственная точка отрисовки выбора и живой ноды; карточки не пересоздаются.
- **`_ClickFrame`**: тап = (нажатие на этой карточке или свежий второй тап) + неподвижный скролл + слоп 12 px.
- **Флаги**: `flag_code()` по коду из подписи, `flag_pixmap()` из `flags/<CODE>.png`, фолбэк — код страны.

### Data Flow
тап → интент → `set N` (бэкенд пишет `selected-server.json` первым) → подтверждение файлом → снятие интента.
Полл `status-json` → `server_tag` → применим только при отсутствии интента и вне settle-окна.
<!-- /ANCHOR:architecture -->

---

<!-- ANCHOR:affected-surfaces -->

## FIX ADDENDUM: AFFECTED SURFACES
| Surface | Current Role | Action | Verification |
|---------|--------------|--------|--------------|
| `MainWindow._select_server_idx` | ставит интент + оптимистичная подсветка | update | тесты двойного тапа (150/250 мс) |
| `MainWindow._select_done` | завершение операции выбора | update (не читать файл при наличии очереди; settle 2 с) | бурст снимков после двойного тапа |
| `MainWindow._status_loaded` | полл статуса | update (не перебивать интент/очередь/окно) | внешний `set N` + снимок |
| `MainWindow.render_servers` / `_paint_selection` | отрисовка сетки и выбора | update (in-place) | снимок + отсутствие пересоздания |
| `_ClickFrame.mouseReleaseEvent` | тап vs скролл | update (DblClick + bounded press-less release) | тест «overscroll при неизменном скролле» |
| `flags/DE.png` | ассет флага | create | пиксельная проверка клетки флага |
| control-plane скрипты / Decky-панель | вне правки | audit-only | отчёты ревьюеров + отдельные фиксы при подтверждении |

Инварианты: выбор никогда не включает VPN; жест никогда не меняет выбор; живая нода ≠ выбор.
<!-- /ANCHOR:affected-surfaces -->

---

<!-- ANCHOR:phases -->

## 4. IMPLEMENTATION PHASES

### Phase 1: Диагностика (выполнено)
- [x] Интент/полл-гонка воспроизведена и объяснена
- [x] Измерено поведение Qt на быстрый второй тап (спай событий)
- [x] Подтверждён отсутствующий флаг DE и источник набора флагов

### Phase 2: Правки
- [x] Интент выбора + settle-окно
- [x] `_paint_selection()` вместо пересборки сетки
- [x] Тап-логика: DblClick + ограниченный «отпуск без нажатия»
- [x] `flags/DE.png` + фолбэк с кодом страны
- [ ] Аудит-фиксы по отчётам ревьюеров

### Phase 3: Проверка
- [ ] Приёмочный прогон `verify039c` (тапы любой скорости, жесты, внешний выбор)
- [ ] Регресс: свайпы вертикальные/горизонтальные, `hRange = 0`, флаг DE
- [ ] Документы, CHANGES.md, коммит и пуш
<!-- /ANCHOR:phases -->

---

<!-- ANCHOR:testing -->

## 5. TESTING STRATEGY

| Test Type | Scope | Tools |
|-----------|-------|-------|
| Инъекция тач-событий | одиночный/двойной тап, свайпы, overscroll | uinput (`hermes-test-touch`) |
| Снимки окна | подсветка выбора, флаг | хук `gui-action.json` + разбор пикселей |
| Проба геометрии | горизонтальные диапазоны страниц | offscreen-импорт модуля GUI |
| Аудит | статический разбор трёх слоёв | три read-only ревьюера |
<!-- /ANCHOR:testing -->

---

<!-- ANCHOR:dependencies -->

## 6. DEPENDENCIES

| Dependency | Type | Status | Impact if Blocked |
|------------|------|--------|-------------------|
| Clash API `:9090` | Internal | Green | OFF → нет метки живой ноды |
| `selected-server.json` | Internal | Green | нет файла → нет подсветки |
| SSH на 192.168.3.2 | External | Green | нет деплоя/проверки |
<!-- /ANCHOR:dependencies -->

---

<!-- ANCHOR:rollback -->

## 7. ROLLBACK PLAN

- **Trigger**: тап перестал работать; выбор меняется жестом; флаг ломает вёрстку карточки.
- **Procedure**: живая копия — `/home/m26/AI/neodon-vpn/neodon-vpn.py.pre038` (для 039 держим свежий бэкап `.pre039`),
  рестарт `neodon-gui-live.service`; репо — `git checkout -- neodon-vpn.py tests/app/neodon-vpn.py`.
<!-- /ANCHOR:rollback -->

---

<!-- ANCHOR:effort -->

## L2: PHASE DEPENDENCIES

| Phase | Depends on | Blocks |
|-------|------------|--------|
| Диагностика | доступ к устройству и хуку снимков | правки (без измерений это было бы гадание) |
| Правки GUI | диагностика | приёмку |
| Аудит | читаемое состояние репозитория | фиксы аудита (правки GUI не блокирует) |
| Фиксы control-plane | подтверждение находки про `off` | живую проверку `off` |
| Приёмка | правки и деплой | коммит и релиз |
<!-- /ANCHOR:phase-deps -->

---

<!-- ANCHOR:enhanced-rollback -->

## L2: EFFORT ESTIMATION

| Phase | Effort | Notes |
|-------|--------|-------|
| Диагностика (спай событий, гэпы, флаги) | ~1.5 ч | три измерительных прохода на устройстве |
| Правки GUI | ~1 ч | интент выбора, `_paint_selection`, тап-логика, ассет |
| Аудит и разбор находок | ~1.5 ч | три ревьюера + собственная проверка каждой находки |
| Фиксы аудита и control-plane | ~1 ч | 9 фиксов, включая честный `off` |
| Приёмка и документы | ~1 ч | синтетический тач, снимки, спека, CHANGES |
<!-- /ANCHOR:effort -->

---

<!-- ANCHOR:phase-deps -->

## L2: ENHANCED ROLLBACK

| Level | Action | Trigger |
|-------|--------|---------|
| GUI | вернуть `neodon-vpn.py.pre039` и перезапустить `neodon-gui-live.service` | тап не работает, подсветка врёт, окно не открывается |
| Репо | `git revert <commit>` либо `git checkout -- neodon-vpn.py tests/app/neodon-vpn.py` | регресс подтверждён тестом |
| Control-plane | вернуть `~/AI/singbox/singbox-toggle.sh.pre039` и выполнить `singbox-toggle.sh off` | `off` не снимает правила или печатает неправду |
| Ассет | удалить `flags/DE.png` (появится код страны) | флаг ломает вёрстку карточки |
| Данные | `selected-server.json` и `raw.json` этой волной не меняются | — |
<!-- /ANCHOR:enhanced-rollback -->
