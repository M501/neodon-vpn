---
title: "Neodon панель Decky: отзывчивое переключени [spec:035-panel-switch-ux]"
description: "Neodon панель Decky: отзывчивое переключение сервера и понятные статусы — мгновенный switching-индикатор, человеческие тексты вместо сырых FAILED/urlopen, ретрай повторного тапа по серверу, TTL transition-маркера 12с, ранняя запись selected-server.json"
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
# Feature Specification: Panel switch UX — отклик и понятные статусы

<!-- SPECKIT_LEVEL: 2 -->
<!-- SPECKIT_TEMPLATE_SOURCE: spec-core | v2.2 -->

---

<!-- ANCHOR:metadata -->
## 1. METADATA

| Field | Value |
|-------|-------|
| **Level** | 2 |
| **Priority** | P1 |
| **Status** | Review (ждёт приёмки владельца) |
| **Created** | 2026-10-04 |
| **Branch** | `035-panel-switch-ux` |
<!-- /ANCHOR:metadata -->

---

<!-- ANCHOR:problem -->
## 2. PROBLEM & PURPOSE

### Problem Statement
Владелец (04.10, живые тыки в Game Mode): смена сервера «применяется через 5–10 с, иногда только со второго тапа»; в панели мелькают сырые состояния (`ON (failed)`) и длинные технические строки в скобках (`refresh: fetch: <urlopen error …>`); после смены на мёртвый сервер панель ~30 с висит в TRANSITIONING, затем DEGRADED без подсказки, watchdog выключает VPN. Журналы 04.10 подтвердили причины: (1) подтверждение UI идёт по 5-с поллам и маркеру `.transitioning` с TTL 30 с; (2) эхо-гвард дропдауна глотает и осознанные повторные тапы по тому же серверу (жалоба «только если повторно нажмёшь на другой»); (3) в скобках статуса печатаются сырые backend-строки; (4) `selected-server.json` пишется только после рестарта сервиса (панель дольше видит старый выбор).

### Purpose
Смена сервера в панели ощущается мгновенной и однозначной: немедленный отклик в UI, человеческие статусы, честный результат — включая явное «server not responding — try another», а повторный тап работает как повторная попытка.
<!-- /ANCHOR:problem -->

---

<!-- ANCHOR:scope -->
## 3. SCOPE

### In Scope
- Панель (index.tsx): мгновенная pending-индикация «switching to <label>…» / «connecting…» / «turning off…» до фактического подтверждения.
- Панель: friendly-маппинг состояний (CONNECTED→connected, FAILED→connection failed, DEGRADED→server not responding и т.д.) + подсказка «try another server» при DEGRADED/FAILED.
- Панель: ретрай-тап — повторный осознанный выбор того же сервера отправляется заново, если статус не CONNECTED; эхо (≤0.8 с после программного изменения) по-прежнему глушится.
- Панель: короткие классифицированные ошибки Refresh вместо сырых urlopen-потрохов; сообщения — отдельной строкой, не в скобках статуса.
- `singbox-toggle.sh`: TTL маркера `.transitioning` 30 с → 12 с (heal-guard 35 с остаётся строго больше).
- `singbox-server.sh`: `selected-server.json` пишется сразу после успешного `sing-box check`, до рестарта сервиса.

### Out of Scope
- Автодетект «мёртвый/живой» сервер и латентность в списке панели — отдельная фича, требует проб на каждый сервер.
- Правки watchdog/heal семантики (internet-first выключение при мёртвом туннеле — работает как задумано).
- Десктопный GUI (neodon-vpn.py) — не меняется в этой итерации.
- Сверка Usage с внешним устройством владельца — вопрос данных, не кода.

### Files to Change

| File Path | Change Type | Description |
|-----------|-------------|-------------|
| decky/neodon-vpn/src/index.tsx | Modify | pending-модель, friendly-статусы, ретрай-тап, notice-строка, shortErr |
| decky/neodon-vpn/dist/index.js (+ .map) | Modify (build) | rollup-сборка из src |
| scripts/singbox-toggle.sh | Modify | TTL маркера 30→12 с |
| scripts/singbox-server.sh | Modify | запись selected-server.json до рестарта |
| singbox-toggle.sh, singbox-server.sh (repo root) | Modify | синк репо-копий |
| CHANGES.md | Modify | запись итерации |
<!-- /ANCHOR:scope -->

---

<!-- ANCHOR:requirements -->
## 4. REQUIREMENTS

### P0 - Blockers (MUST complete)

| ID | Requirement | Acceptance Criteria |
|----|-------------|---------------------|
| REQ-001 | Мгновенный отклик UI: при смене сервера строка статуса сразу показывает «switching to <label>…»; тумблер — «connecting…»/«turning off…». | После тапа строка меняется ≤1 с (не дожидаясь 5-с полла); подтверждение — когда selected==target и состояние финальное, либо таймаут 15 с. |
| REQ-002 | Человеческие статусы: сырые FAILED/DEGRADED/STARTING и т.п. больше не печатаются; при DEGRADED/FAILED — подсказка «try another server». | В панели нет строк со словами FAILED / urlopen / fetch:. DEGRADED→«server not responding», FAILED→«connection failed». |
| REQ-003 | Осознанный повторный тап по тому же серверу отправляет set_server заново, если состояние не CONNECTED; эхо Steam (сразу после обновления prop) — глушится. | journal plugin_loader: тап-тап по мёртвому серверу = 2× set_server; единичное эхо = 0 вызовов. |
| REQ-004 | Ошибки Refresh — короткие и классифицированные: «no network (DNS)», «timeout», «network error»; показываются отдельной строкой ≤8 с. | При недоступном DNS в панели видна короткая строка, без urlopen-текста и без записи в скобки статуса. |

### P1 - Required (complete OR user-approved deferral)

| ID | Requirement | Acceptance Criteria |
|----|-------------|---------------------|
| REQ-005 | TTL маркера `.transitioning` = 12 с в status-json. | После переключения TRANSITIONING держится ≤12 с, далее честное состояние; heal-порог (35 с) > TTL. |
| REQ-006 | `selected-server.json` записывается до рестарта сервиса (после успешного check). | mtime selected ≈ момент check, раньше рестарта; панель видит новый active без задержки; при провале check — откат и selected не пишется. |
<!-- /ANCHOR:requirements -->

---

<!-- ANCHOR:success-criteria -->
## 5. SUCCESS CRITERIA

- **SC-001**: Смена на живой сервер: строка «switching to …» появляется мгновенно, итог CONNECTED ≤8 с, без FAILED-миганий.
- **SC-002**: Смена на мёртвый сервер: «switching to …» → «server not responding» + подсказка; повторный тап перезапускает попытку (подтверждено журналом RPC).
- **SC-003**: В UI за весь сценарий не появляются сырые строки (FAILED/urlopen/fetch:).
<!-- /ANCHOR:success-criteria -->

---

<!-- ANCHOR:risks -->
## 6. RISKS & DEPENDENCIES

| Type | Item | Impact | Mitigation |
|------|------|--------|------------|
| Risk | Ложная классификация эхо-события Steam как осознанного тапа | Лишний set_server (рестарт сервиса) | Окно эхо ≤0.8 с + проверка «value == seen» + только при не-CONNECTED |
| Risk | pending-модель перекроет реальные быстрые состояния | UI показывает stale-строку | Таймаут 15 с + сброс при ok=false + условие «ai==target и финальное состояние» |
| Dependency | Decky RPC (main.py) и status-json | Изменений не требуют | Не трогаем; контракты прежние |
| Risk | Сборка dist на Windows (CRLF) | Панель не загрузится | rollup пишет LF; после заливки — md5-сверка и рестарт plugin_loader |
<!-- /ANCHOR:risks -->

---

<!-- ANCHOR:questions -->

---

<!-- ANCHOR:nfr -->
## L2: NON-FUNCTIONAL REQUIREMENTS

### Performance
- **NFR-P01**: визуальный отклик на тап ≤1 с (следующий React-тик), без ожидания поллов.
- **NFR-P02**: число RPC на действие не растёт (полл 5 с сохраняется).

### Security
- **NFR-S01**: правки только UI/скриптов; секреты не затрагиваются.
- **NFR-S02**: интерполяции shell-команд не добавляются.

### Reliability
- **NFR-R01**: при закрытии/ремоунте панели состояние восстанавливается из тех же файлов (status-json/selected-server.json).
- **NFR-R02**: все изменения обратимы — бэкапы файлов на устройстве + git revert в репо.
<!-- /ANCHOR:nfr -->

---

<!-- ANCHOR:edge-cases -->
## L2: EDGE CASES

### Data Boundaries
- Пустой список серверов: switchServer no-op (уже есть).
- selected отсутствует в raw.json: ai=-1, дропдаун не сбрасывается.

### Error Scenarios
- set_server ok=false (timeout): pending сбрасывается, в notice — короткая ошибка.
- Ремоунт панели во время переключения: pending теряется, статус подхватит TRANSITIONING из маркера.

### State Transitions
- Смена сервера при OFF: pending «switching…» завершается сразу (desired==off), строка возвращается к off.
- DEGRADED→CONNECTED после оживления сервера: подсказка исчезает автоматически.
<!-- /ANCHOR:edge-cases -->

---

<!-- ANCHOR:complexity -->
## L2: COMPLEXITY ASSESSMENT

| Dimension | Score | Notes |
|-----------|-------|-------|
| Scope | 12/25 | 3 файла кода + бандл + репо-копии |
| Risk | 10/25 | UX-логика на живом устройстве, обратимые правки |
| Research | 2/20 | Диагноз уже собран по журналам |
| **Total** | **24/70** | **Level 2** |
<!-- /ANCHOR:complexity -->

---

## 10. OPEN QUESTIONS

- Нет открытых по скоупу. Вне скоупа: сверка Usage с числом владельца; авто-подсказка о watchdog-OFF.
<!-- /ANCHOR:questions -->
