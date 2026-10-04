---
title: "Neodon панель Decky: отзывчивое переключени [spec:035-panel-switch-ux]"
description: "Neodon панель Decky: отзывчивое переключение сервера и понятные статусы — мгновенный switching-индикатор, человеческие тексты вместо сырых FAILED/urlopen, ретрай повторного тапа по серверу, TTL transition-маркера 12с, ранняя запись selected-server.json"
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
# Implementation Plan: Panel switch UX

<!-- SPECKIT_LEVEL: 2 -->
<!-- SPECKIT_TEMPLATE_SOURCE: plan-core | v2.2 -->

---

<!-- ANCHOR:summary -->
## 1. SUMMARY

### Technical Context

| Aspect | Value |
|--------|-------|
| **Language/Stack** | TypeScript (TSX, React 18) + Bash |
| **Framework** | Decky Loader QAM panel (rollup, @decky/ui) |
| **Storage** | Files: `.mode`, `.desired`, `.transitioning`, `selected-server.json`, `sub-cache.json` |
| **Testing** | rollup build + bash -n + живой прогон на устройстве + journal plugin_loader |

### Overview
Панель переходит на локальную модель «pending → подтверждение»: клик сразу отображается («switching to …»), гварды различают эхо Steam (≤0.8 с) и осознанный повтор, статусы маппятся в человеческие, ошибки Refresh классифицируются. Скрипты получают TTL маркера 12 с и раннюю персистенцию selected-server.json. Backend-контракты (main.py, status-json) не меняются.
<!-- /ANCHOR:summary -->

---

<!-- ANCHOR:quality-gates -->
## 2. QUALITY GATES

### Definition of Ready
- [x] Диагноз по журналам 04.10 собран (журнал плагина, journal sing-box, transitions.log, скан серверов)
- [x] Границы скоупа зафиксированы (панель + 2 скрипта; watchdog/десктоп — вне)
- [x] Инструменты деплоя проверены (ssh_exec/put_file, md5-сверка, рестарт plugin_loader)

### Definition of Done
- [ ] Все acceptance criteria REQ-001..006 подтверждены живьём
- [ ] rollup build зелёный; md5 устройство==репо
- [ ] CHANGES.md + commit + push (API) + питфолы в скилл
<!-- /ANCHOR:quality-gates -->

---

<!-- ANCHOR:architecture -->
## 3. ARCHITECTURE

### Pattern
Тонкий UI над file-backed backend: React-панель ↔ Decky RPC (main.py, без изменений) ↔ bash-скрипты и файлы состояния.

### Key Components
- **index.tsx (Content)**: полл 5 с; новый `pendRef` (pending-команда), `notice` (временные сообщения), `progSrvTsRef` (момент программного изменения dropdown), `stRef` (последний actual_state), `FRIENDLY`-маппинг, `shortErr()`.
- **singbox-toggle.sh status-json**: TTL маркера `.transitioning` 30→12 с (heal-guard остаётся 35 с — строго больше).
- **singbox-server.sh**: перенос записи `selected-server.json` сразу после успешного `sing-box check` (до рестарта).

### Data Flow
Тап → switchServer: pend=«switching to X» → RPC set_server → main.py запускает server.sh (патч 3 конфигов, check, selected, рестарт) → полл status-json → ai==target && финальное состояние → pending снят, строка = friendly(actual).
<!-- /ANCHOR:architecture -->

---

<!-- ANCHOR:affected-surfaces -->
## FIX ADDENDUM: AFFECTED SURFACES

| Surface | Current Role | Action | Verification |
|---------|--------------|--------|--------------|
| index.tsx render (строка статуса) | потребитель meta/actual/ip | update: friendly-строки + pending-оверрайд | grep 'FAILED' в dist отсутствует; живой скан |
| switchServer / onToggle | producer RPC | update: ретрай-тап, pendRef | journal plugin_loader: пары set_server/vpn_up |
| refresh (poll) | consumer selected/status | update: снятие pending, приоритет friendly | `actual_state` не печатается в UI напрямую |
| singbox-toggle.sh status-json | producer `.transitioning` | update: TTL 12 с | `stat` маркера + наблюдение TRANSITIONING ≤12 с |
| neodon-heal.sh guard | consumer маркера (≤35 с) | unchanged: 35 > 12 | grep '35' в heal; рестарт-тест |
| singbox-server.sh | producer selected-server.json | update: запись до рестарта | mtime selected < mtime старта юнита (journal) |

Required inventories:
- Same-class producers: `grep -n 'transitioning' ~/AI/singbox/*.sh` (status-json — единственный deleter; heal/toggle — читатели/писатели).
- Consumers of selected-server.json: `grep -rn 'selected-server' repo` (main.py панели, status-json, десктоп-гуй).
- Matrix axes: режим (smart/full/off) × сервер (живой/мёртвый) × действие (тап сервера/тумблер/refresh).
- Algorithm invariant: pending снимается только при подтверждении (ai==target И финальное состояние) или таймауте 15 с; эхо не продлевает pending.
<!-- /ANCHOR:affected-surfaces -->

---

<!-- ANCHOR:phases -->
## 4. IMPLEMENTATION PHASES

### Phase 1: Setup
- [x] Спека 035 создана (spec-new, validate PASSED)
- [x] Диагноз и md5-база сняты
- [ ] Бэкапы целевых файлов на устройстве (cp .bak-20261004)

### Phase 2: Core Implementation
- [ ] index.tsx: pendRef/notice/shortErr/FRIENDLY/ретрай-тап
- [ ] rollup build (dist/index.js + map)
- [ ] singbox-toggle.sh: TTL 30→12
- [ ] singbox-server.sh: selected до рестарта
- [ ] Синк корневых репо-копий

### Phase 3: Verification
- [ ] Живой прогон на устройстве: set_server (живой+мёртвый), TTL, магазин
- [ ] journal plugin_loader: пары вызовов, отсутствие фантомов
- [ ] CHANGES.md, git commit, push via API, питфолы в скилл
<!-- /ANCHOR:phases -->

---

<!-- ANCHOR:testing -->
## 5. TESTING STRATEGY

| Test Type | Scope | Tools |
|-----------|-------|-------|
| Build | rollup, tsc | `npm run build` (Windows, node 26) |
| Syntax | bash -n для скриптов | bash -n |
| Integration | живой set_server на живой и мёртвый сервер; TTL маркера | ssh + journal plugin_loader + stat |
| Manual | сценарий владельца: тап-смена, повторный тап, Refresh | панель QAM (владелец), журнал RPC |
<!-- /ANCHOR:testing -->

---

<!-- ANCHOR:dependencies -->
## 6. DEPENDENCIES

| Dependency | Type | Status | Impact if Blocked |
|------------|------|--------|-------------------|
| Decky Loader (plugin_loader) | Internal | Green | Без рестарта не подхватится новый бандл |
| Устройство онлайн (SSH) | Internal | Green | Не задеплоить/не проверить живьём |
| GitHub push via API | External | Green (token в .env) | Коммит локально, push позже |
<!-- /ANCHOR:dependencies -->

---

<!-- ANCHOR:rollback -->
## 7. ROLLBACK PLAN

- **Trigger**: регресс панели/скриптов на живом устройстве (не переключается, зависает UI).
- **Procedure**: вернуть файлы из `*.bak-20261004` на устройстве; рестарт `plugin_loader`; md5-сверка с git HEAD; при необходимости — `git revert`.
<!-- /ANCHOR:rollback -->

---

<!-- ANCHOR:phase-deps -->
## L2: PHASE DEPENDENCIES

```
Phase 1 (Setup) ──► Phase 2 (Core) ──► Phase 3 (Verify)
```

| Phase | Depends On | Blocks |
|-------|------------|--------|
| Setup | None | Core |
| Core | Setup | Verify |
| Verify | Core | None |
<!-- /ANCHOR:phase-deps -->

---

<!-- ANCHOR:effort -->
## L2: EFFORT ESTIMATION

| Phase | Complexity | Estimated Effort |
|-------|------------|------------------|
| Setup | Low | done (спека+диагноз) |
| Core Implementation | Med | ~1-2 часа |
| Verification | Low | ~30-60 мин |
| **Total** | | **~2-3 часа** |
<!-- /ANCHOR:effort -->

---

<!-- ANCHOR:enhanced-rollback -->
## L2: ENHANCED ROLLBACK

### Pre-deployment Checklist
- [x] Бэкапы будут созданы перед деплоем (cp *.bak-20261004)
- [x] md5-фиксация текущих рабочих версий (снята)
- [ ] journal plugin_loader — контроль после рестарта

### Rollback Procedure
1. Вернуть index.tsx/dist + скрипты из бэкапов устройства.
2. `sudo systemctl restart plugin_loader.service`.
3. Проверить статус-json и панель (юзерский путь).
4. Сообщить владельцу.

### Data Reversal
- **Has data migrations?** No
- **Reversal procedure**: N/A (файлы состояния перезаписываются штатно)
<!-- /ANCHOR:enhanced-rollback -->
