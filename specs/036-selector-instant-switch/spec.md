---
title: "Selector instant switch [spec:036-selector-instant-switch]"
description: "Mini phase 1: selector + urltest + Clash API — мгновенное переключение сервера без рестарта, авто-выбор живого (selector тега proxy, apply preferred при старте, killswitch все ноды)"
trigger_phrases:
  - "feature"
  - "specification"
  - "selector"
importance_tier: "normal"
contextType: "general"
_memory:
  continuity:
    packet_pointer: "specs/036-selector-instant-switch"
    last_updated_at: "2026-10-04T06:00:00Z"
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
# Feature Specification: Selector instant switch (mini phase 1)

<!-- SPECKIT_LEVEL: 2 -->
<!-- SPECKIT_TEMPLATE_SOURCE: spec-core | v2.2 -->

---

<!-- ANCHOR:metadata -->
## 1. METADATA

| Field | Value |
|-------|-------|
| **Level** | 2 |
| **Priority** | P0 |
| **Status** | Complete (приёмка владельца за ним) |
| **Created** | 2026-10-04 |
| **Branch** | `036-selector-instant-switch` |
<!-- /ANCHOR:metadata -->

---

<!-- ANCHOR:problem -->
## 2. PROBLEM & PURPOSE

### Problem Statement
Владелец (ночь 04.10, повторно): «меняю сервер — 10 секунд ничего не происходит, потом меняется; будто ничего не произошло». Факты: бэкенд `set_server` занимал 0.6 с, но полный путь (патч 3 JSON → check → restart сервиса → маркеры → settle в UI) растягивал визуальное переключение на 10–20+ с, а мёртвый сервер давал DEGRADED-лимбо до минуты.

### Purpose
Смена сервера — мгновенная операция ≥0.1 с: sing-box selector переключается через Clash API без рестарта, без маркеров, без TRANSITIONING; авто-выбор живого через urltest.
<!-- /ANCHOR:problem -->

---

<!-- ANCHOR:scope -->
## 3. SCOPE

### In Scope
- Миграция 3 живых конфигов: 12 нод (n0..n11) + urltest `auto` + selector тега **`proxy`** (all: n0..n11+auto, default auto) — нулевой дифф для route.rules/profiles/dns (они уже указывают на `proxy`).
- Clash API (127.0.0.1:9090) + cache_file (выбор селектора переживает рестарты).
- `singbox-server.sh`: `set N` = PUT /proxies/proxy {"name":"nN"} (+ персист .preferred-server/selected-server.json; фоллбэк: рестарт активного юнита, если API недоступен; при OFF — просто сохранить выбор).
- `singbox-toggle.sh`: `apply_pref` после старта smart/full/proxy (применяет .preferred-server).
- `killswitch.sh`: allowlist для FULL включает IP ВСЕХ нод (без break) — иначе fail-closed режет auto-переключения.
- Панель: key-ремаунт дропдауна серверов при смене srvIdx (страховка от залипания отображения).

### Out of Scope
- Manager/фаза-2 (авто-failover при смерти ручного выбора), DNS-развязка (фаза-1b), refresh-антибот (сделан отдельно, CHANGES 62/63).

### Files to Change

| File Path | Change Type | Description |
|-----------|-------------|-------------|
| scripts/singbox-server.sh | Rewrite | PUT-переключатель вместо патч+рестарт |
| scripts/singbox-toggle.sh | Modify | apply_pref в smart/full/proxy |
| killswitch.sh (live) | Modify | endpoint_host → все vless-ноды |
| decky/neodon-vpn/src/index.tsx (+dist) | Modify | key для дропдауна серверов |
| ~/AI/singbox/{config,config-proxy,config-full}.json | Migrate | 12 нод + auto + selector(proxy) + clash_api + cache_file |
| migrate_selector.py (устройство) | Create | разовая миграция с check и бэкапами |
<!-- /ANCHOR:scope -->

---

<!-- ANCHOR:requirements -->
## 4. REQUIREMENTS

### P0 - Blockers (MUST complete)

| ID | Requirement | Acceptance Criteria |
|----|-------------|---------------------|
| REQ-001 | Смена сервера мгновенная и без рестарта | `set N` ≤ 1 с (замер), активный юнит не рестартует, exit_ip меняется |
| REQ-002 | Селектор тега `proxy` сохранён (нулевой дифф для правил/профилей/DNS) | route.final=proxy, dns.remote detour=proxy — работают без правок |
| REQ-003 | Авто-выбор живого по умолчанию | default=auto; urltest (api.ipify.org, 60s, tolerance 100) |
| REQ-004 | Выбор переживает рестарт/OFF→ON | .preferred-server применяется при старте (apply_pref); cache_file включён |

### P1 - Required

| ID | Requirement | Acceptance Criteria |
|----|-------------|---------------------|
| REQ-005 | FULL killswitch не режет живые ноды | allowlist содержит IP всех 12 нод |
| REQ-006 | Панель: дропдаун не залипает на старом значении | key-ремаунт при смене srvIdx |
<!-- /ANCHOR:requirements -->

---

<!-- ANCHOR:success-criteria -->
## 5. SUCCESS CRITERIA

- **SC-001**: set 1 (NL) — 0.10 с, exit 203.188.180.46; set 0 (PL) — 0.09 с, exit 94.183.209.102 (живой прогон 04.10 06:0x).
- **SC-002**: Clash API отвечает: {"type":"Selector","name":"proxy","now":"nN","all":[n0..n11,auto]}.
- **SC-003**: VPN поднимается после OFF→ON за ~4 с (apply_pref), CONNECTED стабилен.
<!-- /ANCHOR:success-criteria -->

---

<!-- ANCHOR:risks -->
## 6. RISKS & DEPENDENCIES

| Type | Item | Impact | Mitigation |
|------|------|--------|------------|
| Risk | Конфиги с selector не пройдут check | Сервис не поднимется | check на tmp + бэкапы .pre-sel-20261004; откат cp |
| Risk | Clash API залочен | PUT не сработает | listen 127.0.0.1:9090; секрет не требуется (локально) |
| Risk | Старый код где-то патчит "proxy"-ноду | Ручной фоллбэк бесполезен | фоллбэк переключён на рестарт+PUT |
<!-- /ANCHOR:risks -->

---

<!-- ANCHOR:questions -->

---

<!-- ANCHOR:nfr -->
## L2: NON-FUNCTIONAL REQUIREMENTS

### Performance
- **NFR-P01**: set_server ≤ 1 с (факт: 0.09–0.10 с).
- **NFR-P02**: без рестарта ядра — соединения не рвутся (interrupt_exist_connections=false).

### Reliability
- **NFR-R01**: при OFF выбор сохраняется и применяется при включении.
- **NFR-R02**: откат — `cp config*.json.pre-sel-20261004` + старые скрипты `.bak-20261004-sel`.
<!-- /ANCHOR:nfr -->

---

<!-- ANCHOR:edge-cases -->
## L2: EDGE CASES

### Data Boundaries
- Некорректный индекс: «ОШИБКА: сервер N не найден» (rc=1).
- API недоступен при активном сервисе: рестарт активного юнита + повторный PUT.

### State Transitions
- OFF: только запись выбора (apply_pref при включении).
- Все ноды мертвы: urltest не находит живого → CONNECTED недостижим (DEGRADED) — как раньше, watchdog работает.
<!-- /ANCHOR:edge-cases -->

---

<!-- ANCHOR:complexity -->
## L2: COMPLEXITY ASSESSMENT

| Dimension | Score | Notes |
|-----------|-------|-------|
| Scope | 15/25 | 3 конфига + 3 скрипта + панель |
| Risk | 14/25 | ядро dataplane; бэкапы/чек/откат |
| Research | 3/20 | факты из доков sing-box 1.14 |
| **Total** | **32/70** | **Level 2** |
<!-- /ANCHOR:complexity -->

---

## 10. OPEN QUESTIONS

- Приёмка владельца: смена сервера из QAM, магазин, реакция на мёртвый сервер.
<!-- /ANCHOR:questions -->
