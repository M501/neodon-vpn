---
title: "VPN status hardening: bounded probes + intent switch [spec:034-vpn-status-hardening]"
description: "VPN status hardening: bounded probes + intent switch"
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
    packet_pointer: "specs/034-vpn-status-hardening"
    last_updated_at: "2026-10-03T22:10:00Z"
    last_updated_by: "hermes-main"
    recent_action: "Implemented + verified live (034)"
    next_safe_action: "None - complete"
    blockers: []
    key_files: []
    session_dedup:
      fingerprint: "sha256:f8c35e8af966969c48ef6983eddc4e408af39d552e36b07983976284f4d32186"
      session_id: "main-20261003"
      parent_session_id: null
    completion_pct: 100
    open_questions: []
    answered_questions: []
---
# Feature Specification: VPN status hardening — bounded probes + intent switch

<!-- SPECKIT_LEVEL: 2 -->
<!-- SPECKIT_TEMPLATE_SOURCE: spec-core | v2.2 -->

---

<!-- ANCHOR:metadata -->
## 1. METADATA

| Field | Value |
|-------|-------|
| **Level** | 2 |
| **Priority** | P0 |
| **Status** | In Progress |
| **Created** | 2026-10-04 |
| **Branch** | `034-vpn-status-hardening` |
<!-- /ANCHOR:metadata -->

---

<!-- ANCHOR:problem -->
## 2. PROBLEM & PURPOSE

### Problem Statement
Живая диагностика 03.10 (CachyOS/Ally X): при выбранном мёртвом сервере #4 (DE, grpc/tls — не отвечает со стороны провайдера) `status-json` в «отравленном» состоянии висел >40 с (неограниченный DNS-resolve в python-пробе latency; внешние пробы без обёртки `timeout`) — плагин каждые 5 с ловил свой 15-с таймаут, и панель получала «status failed» (шторм ложных FAILED вместо честного состояния). Тумблер панели следовал за фактическим состоянием: при TRANSITIONING/FAILED он флипал позицию, Steam пере-испускал onChange → фантомные vpn_up/vpn_down, ре-коннект-цикл и обнуление счётчика времени.

В ходе живой верификации вскрыты два корневых дефекта, объясняющих исходную жалобу «сменил сервер — всё сломалось»: (1) пикер `singbox-server.sh` собирал proxy-аутбаунд без `domain_resolver: "local"` — после любой смены сервера резолв адреса сервера уходил в петлю через прокси (`DNS query loopback in transport[remote]`) и DNS умирал на всей машине; (2) `neodon-heal.sh`, срабатывая из ExecStopPost при рестарте (смена сервера), затирал `.mode`→off и resolv прямо в момент перезапуска.

### Purpose
Статус-панель и плагин остаются честными и отзывчивыми при мёртвом сервере: ограниченный по времени статус (без таймаут-шторма), тумблер = намерение пользователя (без фантомных вызовов), рабочий сервер по умолчанию.
<!-- /ANCHOR:problem -->

---

<!-- ANCHOR:scope -->
## 3. SCOPE

### In Scope
- `scripts/singbox-toggle.sh` (status-json): жёсткие bounds (`timeout N`) на все внешние пробы — curl exit-probe, python latency, чтение watchdog-state, firewall dump.
- Decky backend `main.py`: таймаут get_status 15 → 30 с.
- Панель `src/index.tsx`: тумблер следует за `desired_mode` (интентом), фейл-полл не гадает OFF; таймер не взводится при FAILED/LOCKED.
- Live-деплой на устройство, переключение выбранного сервера на рабочий (#0 PL), живая верификация (healthy CONNECTED; мёртвый сервер → bounded FAILED ≤ ~20 с).
- `scripts/singbox-server.sh`: `domain_resolver: "local"` в proxy-аутбаунде (bootstrap) + патч `config-proxy.json` + маркер `.transitioning` перед рестартами.
- `scripts/neodon-heal.sh`: restart-guard по свежему маркеру + guard substate auto-restart.
- CHANGES.md, синк репо-копий (root toggle/server, watchdog репо←live, heal), питфолы в скилле.

### Out of Scope
- Ремонт мёртвых серверов #4/#5/#9 (сторона провайдера) — только выбор рабочих.
- Класс-фикс «remote-DNS только для proxied-доменов» (спека 033) — отдельная работа.
- Desktop GUI `neodon-vpn.py` — его статус-логика не меняется.

### Files to Change

| File Path | Change Type | Description |
|-----------|-------------|-------------|
| `scripts/singbox-toggle.sh` | Modify | bounds (`timeout`) всех внешних проб status-json |
| `decky/neodon-vpn/main.py` | Modify | get_status timeout 15→30 с |
| `decky/neodon-vpn/src/index.tsx` | Modify | switch = intent (dm); таймер не взводится на FAILED/LOCKED |
| `decky/neodon-vpn/dist/index.js` | Modify (build) | пересборка бандла (rollup) |
| `singbox-toggle.sh` (root) | Modify | root-копия = scripts/ (LF) |
| `scripts/neodon-watchdog.sh` | Modify | порт live-версии (smart + direct-probe) в репо |
| `scripts/singbox-server.sh` | Modify | domain_resolver bootstrap + config-proxy + маркер |
| `scripts/neodon-heal.sh` | Modify | restart-guard (маркер + auto-restart) |
| `singbox-server.sh` (root) | Modify | root-копия = scripts/ |
| `CHANGES.md` | Modify | запись 034 |
<!-- /ANCHOR:scope -->

---

<!-- ANCHOR:requirements -->
## 4. REQUIREMENTS

### P0 - Blockers (MUST complete)

| ID | Requirement | Acceptance Criteria |
|----|-------------|---------------------|
| REQ-001 | При мёртвом сервере `status-json` завершается ≤20 с и rc=0 (валидный JSON) | живой прогон с сервером #4: `time bash toggle status-json` → JSON (FAILED/DEGRADED) за ≤20 с |
| REQ-004 | После смены сервера DNS и VPN-состояние живы: `.mode` сохраняется, туннель поднимается на новом сервере | `server.sh set 1` при smart → `mode=smart`, CONNECTED (NL) за ≤6 с; в transitions нет новых smart-to-off |

### P1 - Required (complete OR user-approved deferral)

| ID | Requirement | Acceptance Criteria |
|----|-------------|---------------------|
| REQ-002 | Панель не флипает тумблер при TRANSITIONING/FAILED; нет фантомных vpn_up/vpn_down | код: `nowOn = ok ? dm!=="off" : seenRef.current`; журнал plugin_loader: при статус-шторме мутаций нет |
| REQ-003 | Выбранный сервер — рабочий (#0 PL); конфиги и selected-server согласованы | `bash singbox-server.sh set 0` → `toggle smart` → CONNECTED (exit 94.183.x) |
| REQ-005 | heal не чистит во время рестарта (смена сервера) | switch-тест: после set1/set0 нет HEAL-строк, resolv не восстанавливается раньше времени |
<!-- /ANCHOR:requirements -->

---

<!-- ANCHOR:success-criteria -->
## 5. SUCCESS CRITERIA

- **SC-001**: при мёртвом сервере статус отвечает за ≤20 с (было >40 с) и панель показывает честный FAILED без реконнект-шторма.
- **SC-002**: с рабочим сервером полный цикл off→smart→CONNECTED→off проходит; exit = 94.183.209.x (PL).
- **SC-003**: смена сервера в рантайме: NL CONNECTED за 3 с (exit 203.188.180.46), назад PL — 6 с (94.183.209.116); `.mode` остаётся `smart`.
<!-- /ANCHOR:success-criteria -->

---

<!-- ANCHOR:risks -->
## 6. RISKS & DEPENDENCIES

| Type | Item | Impact | Mitigation |
|------|------|--------|------------|
| Dependency | Устройство Ally X по SSH (LAN) | Нет доступа → правки только в репо | Ретрай после включения |
| Risk | Смена сервера задевает живую сессию | Low | VPN off по умолчанию; после тестов — вернуть off |
| Risk | Bounds timeouts дают ложный FAILED на медленной сети | Low | fast=3с/retry=6с сохранены; добавлены лишь внешние bounds |
<!-- /ANCHOR:risks -->

---

<!-- ANCHOR:questions -->

---

<!-- ANCHOR:nfr -->
## L2: NON-FUNCTIONAL REQUIREMENTS

### Performance
- **NFR-P01**: status-json ≤1 с healthy, ≤20 с worst-case (мёртвый сервер).
- **NFR-P02**: панель: не более одного статус-опроса в 5 с; мутаций из опроса — ноль.

### Security
- **NFR-S01**: без изменений в аутентификации; секреты не трогаем.
- **NFR-S02**: без изменений в защите данных.

### Reliability
- **NFR-R01**: статус всегда rc=0 c валидным JSON (при живом bash).
- **NFR-R02**: фейл-полл панели не порождает мутаций (ноль фантомных вызовов).
<!-- /ANCHOR:nfr -->

---

<!-- ANCHOR:edge-cases -->
## L2: EDGE CASES

### Data Boundaries
- Empty input: пустой watchdog-state → wd_fails=0 (прежнее поведение).
- Maximum length: не применимо (нет пользовательского ввода).
- Invalid format: невалидный JSON конфигов ловит `sing-box check` до применения.

### Error Scenarios
- External service failure: мёртвый сервер → state FAILED/DEGRADED, без «status failed».
- Network timeout: все пробы bounded (`timeout`); статус возвращается всегда.
- Concurrent access: status-json не держит mutex (как было).

### State Transitions
- Partial completion: TRANSITIONING (маркер ≤15 с) не флипает тумблер; STOPPING/off корректно показывает Off.
- Session expiry: не применимо.
<!-- /ANCHOR:edge-cases -->

---

<!-- ANCHOR:complexity -->
## L2: COMPLEXITY ASSESSMENT

| Dimension | Score | Notes |
|-----------|-------|-------|
| Scope | 8/25 | 3 файла продукта + деплой + репо-синк |
| Risk | 10/25 | смена дефолтного сервера — обратима одним set |
| Research | 5/20 | живая диагностика; внешний ресёрч не нужен |
| **Total** | **23/70** | **Level 2** |
<!-- /ANCHOR:complexity -->

---

## 10. OPEN QUESTIONS

- Почему [4]/[5]/[9] не отвечают именно с этой сети (провайдер vs DPI-фрагментация) — UNKNOWN, вне скоупа; рабочий список PL/NL/SW/AT/IS.
<!-- /ANCHOR:questions -->

---

<!--
CORE TEMPLATE (~80 lines)
- Essential what/why/how only
- No boilerplate sections
- Add L2/L3 addendums for complexity
-->