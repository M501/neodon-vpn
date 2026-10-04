---
title: "Selector instant switch [spec:036-selector-instant-switch]"
description: "Mini phase 1: selector + urltest + Clash API — мгновенное переключение сервера без рестарта, авто-выбор живого"
trigger_phrases:
  - "implementation"
  - "plan"
importance_tier: "normal"
contextType: "general"
_memory:
  continuity:
    packet_pointer: "specs/036-selector-instant-switch"
    last_updated_at: "2026-10-04T06:00:00Z"
    last_updated_by: "hermes-main"
    recent_action: "Plan filled"
    next_safe_action: "Verify"
    blockers: []
    key_files: []
    session_dedup:
      fingerprint: "sha256:66fe3c95194e019c99a60246f874f5ec63dae6209757940e62ccf55a49e2e7f7"
      session_id: "main-20261004"
      parent_session_id: null
    completion_pct: 9
    open_questions: []
    answered_questions: []
---
# Implementation Plan: Selector instant switch

<!-- SPECKIT_LEVEL: 2 -->
<!-- SPECKIT_TEMPLATE_SOURCE: plan-core | v2.2 -->

---

<!-- ANCHOR:summary -->
## 1. SUMMARY

### Technical Context

| Aspect | Value |
|--------|-------|
| **Language/Stack** | sing-box 1.14 configs + Bash + TSX (panel) |
| **Mechanism** | Selector outbound (tag `proxy`) + urltest `auto` + Clash API 127.0.0.1:9090 |
| **Testing** | sing-box check ×3 + живой прогон (тайминги set, exit_ip) |

### Overview
Единственное изменение топологии: outbounds конфигов становятся [n0..n11, auto, proxy(selector), direct, block], при этом тег `proxy` сохраняется как имя селектора — route.rules/profiles/dns/desktop остаются нетронутыми. Смена сервера = PUT /proxies/proxy. `apply_pref` в toggle восстанавливает выбор после OFF→ON; cache_file держит выбор между рестартами.
<!-- /ANCHOR:summary -->

---

<!-- ANCHOR:quality-gates -->
## 2. QUALITY GATES

### Definition of Ready
- [x] Международный факт-чек по докам sing-box 1.14 (selector/urltest/clash api/cache_file)
- [x] Бэкапы и откат продуманы (конфиги .pre-sel-20261004, скрипты .bak-20261004-sel)
- [x] Контракт server.sh `set N` сохранён (панель/десктоп не меняются)

### Definition of Done
- [x] REQ-001..006 подтверждены живьём (кроме приёмки владельца)
- [x] CHANGES.md + commit + push
<!-- /ANCHOR:quality-gates -->

---

<!-- ANCHOR:architecture -->
## 3. ARCHITECTURE

### Pattern
Dataplane owns the choice: sing-box selector — единственный владелец активного outbound; оболочка (server.sh/toggle) — тонкий клиент Clash API; UI — read-only.

### Key Components
- **migrate_selector.py**: одноразовая миграция конфигов (check-gated, atomic, backups).
- **singbox-server.sh**: `set N` → PUT; персист; фоллбэки.
- **singbox-toggle.sh apply_pref**: применение .preferred-server после старта.
- **killswitch.sh**: allowlist всех нод.

### Data Flow
Клик (панель/десктоп) → server.sh set N → PUT /proxies/proxy nN → мгновенный switch → status-json видит новый exit_ip (проба). OFF→ON: toggle → start → apply_pref → PUT → CONNECTED.
<!-- /ANCHOR:architecture -->

---

<!-- ANCHOR:affected-surfaces -->
## FIX ADDENDUM: AFFECTED SURFACES

| Surface | Current Role | Action | Verification |
|---------|--------------|--------|--------------|
| config*.json outbounds | 1 нода `proxy` | update: 12 нод + auto + selector(`proxy`) | sing-box check ×3 PASS |
| route.rules/profiles/dns | ссылаются на `proxy` | unchanged (нулевой дифф) | check PASS + живой трафик |
| server.sh | пач+check+restart | rewrite: PUT | set1=0.10с, set0=0.09с |
| killswitch.sh | 1 IP | update: все vless-ноды | full не тестировался в этом прогоне (перенесено) |
| панель dropdown | без key | update: key-ремаунт | визуальная приёмка владельца |
<!-- /ANCHOR:affected-surfaces -->

---

<!-- ANCHOR:phases -->
## 4. IMPLEMENTATION PHASES

### Phase 1: Setup
- [x] Факт-чек доков; бэкапы; спека 036

### Phase 2: Core Implementation
- [x] migrate_selector.py + прогон (3× check PASS)
- [x] server.sh rewrite; toggle apply_pref; killswitch all-nodes; панель key

### Phase 3: Verification
- [x] Живой прогон: OFF→smart→CONNECTED 4 с; set1 0.10 с; set0 0.09 с; Clash API ok
- [x] md5 синк; plugin_loader рестарт
- [x] CHANGES.md (64) + commit + push
<!-- /ANCHOR:phases -->

---

<!-- ANCHOR:testing -->
## 5. TESTING STRATEGY

| Test Type | Scope | Tools |
|-----------|-------|-------|
| Syntax | sing-box check ×3, bash -n ×2 | sing-box, bash |
| Integration | set N тайминги, exit_ip смена, Clash API | ssh + status-json |
| Manual | панель: смена сервера, дропдаун | владелец |
<!-- /ANCHOR:testing -->

---

<!-- ANCHOR:dependencies -->
## 6. DEPENDENCIES

| Dependency | Type | Status | Impact if Blocked |
|------------|------|--------|-------------------|
| sing-box 1.14 selector/urltest/Clash API | Internal | Green (проверено живьём) | — |
| curl на устройстве | Internal | Green | PUT/фоллбэки |
<!-- /ANCHOR:dependencies -->

---

<!-- ANCHOR:rollback -->
## 7. ROLLBACK PLAN

- **Trigger**: регресс трафика/смены сервера.
- **Procedure**: `cp ~/AI/singbox/config*.json.pre-sel-20261004` обратно; вернуть `*.bak-20261004-sel`; рестарт юнита; (или git revert).
<!-- /ANCHOR:rollback -->

---

<!-- ANCHOR:phase-deps -->
## L2: PHASE DEPENDENCIES

```
Setup ──► Core ──► Verify
```

| Phase | Depends On | Blocks |
|-------|------------|--------|
| Core | Setup | Verify |
| Verify | Core | None |
<!-- /ANCHOR:phase-deps -->

---

<!-- ANCHOR:effort -->
## L2: EFFORT ESTIMATION

| Phase | Complexity | Estimated Effort |
|-------|------------|------------------|
| Core | Med | ~1.5 часа |
| Verify | Low | ~30 мин |
| **Total** | | **~2 часа** |
<!-- /ANCHOR:effort -->

---

<!-- ANCHOR:enhanced-rollback -->
## L2: ENHANCED ROLLBACK

### Pre-deployment Checklist
- [x] Бэкапы конфигов (авто в миграции) и скриптов (.bak-20261004-sel)
- [x] check-gate на каждый кандидат-конфиг
- [x] md5-сверка после деплоя

### Rollback Procedure
1. cp config*.json.pre-sel-20261004 → обратно.
2. Вернуть скрипты .bak-20261004-sel.
3. systemctl --user restart sing-box.service.
4. Проверить status-json.

### Data Reversal
- **Has data migrations?** No (конфиги персистятся, бэкапы на месте)
- **Reversal procedure**: см. выше
<!-- /ANCHOR:enhanced-rollback -->
