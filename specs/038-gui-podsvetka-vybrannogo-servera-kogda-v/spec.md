---
title: "GUI: подсветка выбранного сервера + скролл только вертикальный [spec:038-gui-podsvetka-vybrannogo-servera-kogda-v]"
description: "GUI: подсветка выбранного сервера когда VPN выключен + скролл только вертикальный (тач)"
trigger_phrases:
  - "feature"
  - "specification"
  - "name"
  - "template"
  - "spec core"
importance_tier: "normal"
contextType: "general"
_memory:
  continuity:
    packet_pointer: "specs/038-gui-podsvetka-vybrannogo-servera-kogda-v"
    last_updated_at: "2026-10-05T17:45:00Z"
    last_updated_by: "hermes-main"
    recent_action: "spec.md filled (evidence collected on device)"
    next_safe_action: "Fill plan.md"
    blockers: []
    key_files: []
    session_dedup:
      fingerprint: "sha256:0d62fed10591cd75dd55ff7121bac1859a7b70ba1fb7b0250cbc5c211270aaa7"
      session_id: "main-20261005"
      parent_session_id: null
    completion_pct: 20
    open_questions: []
    answered_questions: []
---
# Feature Specification: подсветка выбранного сервера и вертикальный скролл

<!-- SPECKIT_LEVEL: 1 -->
<!-- SPECKIT_TEMPLATE_SOURCE: spec-core | v2.2 -->

---

<!-- ANCHOR:metadata -->
## 1. METADATA

| Field | Value |
|-------|-------|
| **Level** | 1 |
| **Priority** | P1 |
| **Status** | In Progress |
| **Created** | 2026-10-05 |
| **Branch** | `038-gui-podsvetka-vybrannogo-servera-kogda-v` |
<!-- /ANCHOR:metadata -->

---

<!-- ANCHOR:problem -->
## 2. PROBLEM & PURPOSE

### Problem Statement
Жалоба владельца (десктопный GUI на CachyOS, 05.10): (1) при выключенном VPN нельзя выбрать
сервер «заранее» — тап по карточке даёт «Server switched», но НИ ОДНА карточка визуально не
выделена как выбранная (в v2RayTun выбранный сервер виден всегда); (2) тач-скролл двигает
содержимое страницы влево-вправо — нужно только вверх-вниз.

**Корневые причины (снято с устройства, не гипотезы):**
1. `render_servers()` помечает карточку «active» по `self.active_addr`, а тот берётся из
   `~/AI/singbox/config.json` у аутбаунда `tag=proxy` по ключу `server`. После selector-модели
   (spec 036) `proxy` — это `selector` (`type/outbounds/default`, БЕЗ `server`) во всех трёх
   конфигах ⇒ `active_addr` всегда `None` ⇒ подсветки нет НИКОГДА, ни при ON, ни при OFF.
   Намерение пользователя живёт в `~/AI/singbox/selected-server.json` (его пишет
   `singbox-server.sh set N` ЕЩЁ ДО переключения и при OFF тоже) — GUI его не читает
   (`grep -c selected-server` == 0).
2. Горизонтальный скролл реален и зависит от ширины окна: окно на устройстве 565×543
   (логически), вьюпорт страницы home 498 px, а `content.minimumSizeHint().width()` == 509
   (две колонки карточек: карточка 238 px, потому что подпись `QLabel(server_desc(s))` не
   эллизится и держит полную ширину текста) ⇒ `hRange = 11`; при окне 460 px — уже **116 px**.
   QScroller `TouchGesture` на вьюпорте двигает по обеим осям. Синтетический палец
   (uinput `hermes-test-touch`): свайп влево дал сдвиг содержимого −8 px, вертикальный
   свайп работает (контроль). Остальные страницы при 565 px не переполнены.

### Purpose
Выбранный сервер виден всегда (и его можно выбрать/сменить при OFF), а тач-скролл
структурно ограничен вертикалью на всех страницах.
<!-- /ANCHOR:problem -->

---

<!-- ANCHOR:scope -->
## 3. SCOPE

### In Scope
- Подсветка выбранного сервера (accent-рамка) независимо от состояния VPN.
- Метка фактически применённой ноды в selector-модели (Clash API `GET /proxies/proxy` → `now`).
- Мгновенная визуальная реакция на тап по карточке.
- Синхронизация с панелью Decky: смена сервера из панели видна в десктоп-GUI (источник — `status-json.server_tag`).
- Структурный запрет горизонтального скролла/панорамирования на всех страницах.

### Out of Scope
- Бэкенд (`singbox-toggle.sh` / `singbox-server.sh` / конфиги) — не трогаем.
- Перекомпоновка страниц и новые элементы UI, второе (дублирующее) выделение.
- Автоподключение при выборе сервера — power только тумблером (политика).

### Files to Change

| File Path | Change Type | Description |
|-----------|-------------|-------------|
| `neodon-vpn.py` | Modify | подсветка выбора + метка живой ноды + вертикальный только скролл |
| `tests/app/neodon-vpn.py` | Modify | та же правка (вторая синхронная копия, её берёт `stage.sh`) |
| `CHANGES.md` | Modify | запись об изменении |
<!-- /ANCHOR:scope -->

---

<!-- ANCHOR:requirements -->
## 4. REQUIREMENTS

### P0 - Blockers (MUST complete)

| ID | Requirement | Acceptance Criteria |
|----|-------------|---------------------|
| REQ-001 | Выбранный сервер подсвечен при выключенном VPN | Пиксель-пруф grab-снимка окна при `.mode=off`: карточка выбранного сервера несёт accent-рамку `#3373F7` |
| REQ-002 | Тап по карточке подсвечивает её сразу, в том числе при OFF | После тапа `selected-server.json` и подсветка совпадают с тапнутой карточкой (grab + файл) |
| REQ-003 | Горизонтальное панорамирование невозможно ни на одной странице | `hRange == 0` для каждой страницы при ширине окна 565/820/420; синтетический горизонтальный свайп даёт `dx == 0` |

### P1 - Required (complete OR user-approved deferral)

| ID | Requirement | Acceptance Criteria |
|----|-------------|---------------------|
| REQ-004 | Применённая нода видна и не путается с выбранной | при живом Clash API метка `●` стоит на индексе `n<idx>` из `GET /proxies/proxy` |
| REQ-005 | Выбор из панели Decky отражается в десктоп-GUI | смена `selected-server.json` извне → в пределах одного полла (≤8 с) подсветка переезжает |
| REQ-006 | Вертикальный скролл не сломан | синтетический вертикальный свайп даёт `dy != 0`, страница прокручивается |
<!-- /ANCHOR:requirements -->

---

<!-- ANCHOR:success-criteria -->
## 5. SUCCESS CRITERIA

- **SC-001**: grab-снимок окна при OFF показывает ровно одну карточку с accent-рамкой — это сервер из `selected-server.json`.
- **SC-002**: `hRange == 0` на всех страницах при 565/820/420 px; горизонтальные свайпы вправо и влево не двигают контент (`dx == 0`), вертикальный — двигает.
- **SC-003**: обе repo-копии GUI и живой файл на устройстве совпадают по md5.
<!-- /ANCHOR:success-criteria -->

---

<!-- ANCHOR:risks -->
## 6. RISKS & DEPENDENCIES

| Type | Item | Impact | Mitigation |
|------|------|--------|------------|
| Dependency | Clash API `127.0.0.1:9090` | при OFF API недоступен | `curl -m 1`; недоступность = нет live-метки, выбор всё равно подсвечен |
| Dependency | `selected-server.json` | файла нет (свежая машина) | пустой выбор = подсветки нет, поведение как раньше |
| Risk | Клиппинг подписи при очень узком окне | Низкий | подпись карточки становится эллидящей (как заголовок); проверка на 565/420 px |
| Risk | Живой процесс держит старый код | Средний | рестарт GUI + пиксель-проба grab до/после |
| Risk | Синтетический тач может случайно тапнуть карточку | Низкий | свайпы только по пустым зонам + сверка `selected-server.json` до/после |
<!-- /ANCHOR:risks -->

---

<!-- ANCHOR:questions -->
## 7. OPEN QUESTIONS

- Нет: источник истины выбора определён (`selected-server.json` — его же читает и панель, и `status-json`).
<!-- /ANCHOR:questions -->
