---
title: "VPN status hardening: bounded probes + intent switch [spec:034-vpn-status-hardening]"
description: "VPN status hardening: bounded probes + intent switch"
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
# Implementation Plan: VPN status hardening — bounded probes + intent switch

<!-- SPECKIT_LEVEL: 2 -->
<!-- SPECKIT_TEMPLATE_SOURCE: plan-core | v2.2 -->

---

<!-- ANCHOR:summary -->
## 1. SUMMARY

### Technical Context

| Aspect | Value |
|--------|-------|
| **Language/Stack** | Bash + Python 3 (host), TypeScript/React (Decky-панель) |
| **Framework** | Decky Loader plugin (rollup build) |
| **Storage** | Файлы состояния хоста: .mode, .desired, watchdog-state.json |
| **Testing** | Живые bash-прогоны + validate.sh --strict |

### Overview
Жёстко ограничиваем все внешние пробы status-json (timeout), поднимаем таймаут get_status в плагине до 30 с и переводим тумблер панели на «намерение» (desired_mode). Плюс живьём переключаем дефолтный сервер на рабочий (#0 PL) и верифицируем цикл off→smart→CONNECTED→off и bounded-поведение на мёртвом сервере.
<!-- /ANCHOR:summary -->

---

<!-- ANCHOR:quality-gates -->
## 2. QUALITY GATES

### Definition of Ready
- [ ] Problem statement clear and scope documented
- [ ] Success criteria measurable
- [ ] Dependencies identified

### Definition of Done
- [ ] All acceptance criteria met
- [ ] Tests passing (if applicable)
- [ ] Docs updated (spec/plan/tasks)
<!-- /ANCHOR:quality-gates -->

---

<!-- ANCHOR:architecture -->
## 3. ARCHITECTURE

### Pattern
Thin-wrapper: QAM-панель → python backend → bash CLI (sing-box)

### Key Components
- **QAM-панель (src/index.tsx)**: показывает состояние; тумблер = intent.
- **Decky backend (main.py)**: RPC-обёртки над bash; get_status timeout 30 с.
- **singbox-toggle.sh (status-json)**: оракул состояния; все пробы bounded.
- **neodon-watchdog.sh**: internet-first страховка (не меняется, синк репо).

### Data Flow
Панель раз в 5 с: get_status → bash toggle status-json (bounded пробы) → JSON → панель решает позицию тумблера по desired_mode; ФАКТИЧЕСКОЕ состояние — только в текстовой строке статуса. Мутации — только из действий пользователя.
<!-- /ANCHOR:architecture -->

---

<!-- ANCHOR:affected-surfaces -->
## FIX ADDENDUM: AFFECTED SURFACES

Use this section when `research_intent=fix_bug`, when planning from a deep-review FAIL/CONDITIONAL verdict, or when any finding touches security, path handling, env precedence, schema boundaries, persistence, public responses, or shared policy.

| Surface | Current Role | Action | Verification |
|---------|--------------|--------|--------------|
| singbox-toggle.sh (producer) | владеет внешними пробами | update — bounds | живой прогон: ≤20 с на мёртвом сервере |
| plugin main.py get_status | потребляет status-json | update — timeout 30 | журнал get_status после деплоя |
| Панель src/index.tsx | потребляет actual/desired | update — switch=intent | сборка + журнал (нет фантомов) |
| Desktop GUI neodon-vpn.py | свой оракул | not a consumer | grep status-json в app/ |
| scripts/neodon-watchdog.sh | независимый надзор | unchanged (синк репо) | diff было/стало |
| scripts/singbox-server.sh (пикер) | собирает proxy-аутбаунд | update — domain_resolver + proxy cfg + маркер | switch-тест: NL/PL CONNECTED, нет loopback |
| scripts/neodon-heal.sh | чистит след при мёртвом туннеле | update — restart-guard | transitions: нет smart-to-off при switch |

Required inventories:
- Same-class producers: все внешние вызовы в status-json — grep curl/python3/firewall-cmd в scripts/singbox-toggle.sh → покрыты bounds.
- Consumers of changed symbols: grep -rn "status-json" scripts decky app → panel+RPC (обновлены), GUI (не консьюмер).
- Matrix axes: state(active/inactive) × tunnel(up/down) × mode(smart/full/off/proxy) — в живых прогонах.
- Algorithm invariant: status-json ВСЕГДА завершается за bounded время и печатает валидный JSON; adversarial: мёртвый сервер (DNS-hang), пустой watchdog-state, отсутствие tun0.
<!-- /ANCHOR:affected-surfaces -->

---

<!-- ANCHOR:phases -->
## 4. IMPLEMENTATION PHASES

### Phase 1: Setup
- [x] Бэкапы live-файлов на устройстве (.bak-20261004)
- [x] LF-нормализация файлов
- [x] Baseline зафиксирован (healthy 0.5 с / dead >40 с)

### Phase 2: Core Implementation
- [x] Bounds в status-json (toggle.sh)
- [x] get_status timeout 30 (main.py)
- [x] Switch=intent + timer guard (index.tsx) + пересборка dist
- [x] Пикер: domain_resolver bootstrap + config-proxy + маркер; heal restart-guard

### Phase 3: Verification
- [x] Живой цикл off→smart→CONNECTED→off (PL)
- [x] Dead-server: bounded FAILED ≤20 с (было >40 с)
- [x] CHANGES.md + репо-синк + скилл
<!-- /ANCHOR:phases -->

---

<!-- ANCHOR:testing -->
## 5. TESTING STRATEGY

| Test Type | Scope | Tools |
|-----------|-------|-------|
| Unit | syntax: bash -n, py_compile | bash/python |
| Integration | живой хост: off→smart→status-json тайминги; мёртвый сервер → bounded | ssh + time |
| Manual | журнал plugin_loader: backend up; нет фантомных вызовов | journalctl |
<!-- /ANCHOR:testing -->

---

<!-- ANCHOR:dependencies -->
## 6. DEPENDENCIES

| Dependency | Type | Status | Impact if Blocked |
|------------|------|--------|-------------------|
| Ally X (SSH) | Internal | Green | без него — только репо-правки |
| sing-box 1.14.2 | Internal | Green | не меняется |
| Decky plugin_loader | Internal | Green | рестарт для релоада main.py |
<!-- /ANCHOR:dependencies -->

---

<!-- ANCHOR:rollback -->
## 7. ROLLBACK PLAN

- **Trigger**: после деплоя статус/панель ведут себя хуже базовой линии.
- **Procedure**: вернуть .bak-файлы на устройстве, рестарт plugin_loader, server set 0; в репо — revert.
<!-- /ANCHOR:rollback -->

---


---

<!-- ANCHOR:phase-deps -->
## L2: PHASE DEPENDENCIES

```
Phase 1 (Setup) ──────┐
                      ├──► Phase 2 (Core) ──► Phase 3 (Verify)
Phase 1.5 (Config) ───┘
```

| Phase | Depends On | Blocks |
|-------|------------|--------|
| Setup | None | Core, Config |
| Config | Setup | Core |
| Core | Setup, Config | Verify |
| Verify | Core | None |
<!-- /ANCHOR:phase-deps -->

---

<!-- ANCHOR:effort -->
## L2: EFFORT ESTIMATION

| Phase | Complexity | Estimated Effort |
|-------|------------|------------------|
| Setup | Low | 15 мин |
| Core Implementation | Med | 45 мин |
| Verification | Med | 45 мин |
| **Total** | | **~2-3 часа** |
<!-- /ANCHOR:effort -->

---

<!-- ANCHOR:enhanced-rollback -->
## L2: ENHANCED ROLLBACK

### Pre-deployment Checklist
- [ ] Backup created (if data changes)
- [ ] Feature flag configured
- [ ] Monitoring alerts set

### Rollback Procedure
1. Вернуть toggle.sh из `.bak-20261004` на устройстве.
2. `sudo systemctl restart plugin_loader.service` (релоад main.py).
3. Smoke: `bash toggle off` → internet via ISP (ipify = домашний IP).
4. Сообщить владельцу строкой в отчёте.

### Data Reversal
- **Has data migrations?** No
- **Reversal procedure**: N/A
<!-- /ANCHOR:enhanced-rollback -->

---

<!--
LEVEL 2 PLAN (~140 lines)
- Core + Verification additions
- Phase dependencies, effort estimation
- Enhanced rollback procedures
-->