---
title: "VPN status hardening: bounded probes + intent switch [spec:034-vpn-status-hardening]"
description: "VPN status hardening: bounded probes + intent switch"
trigger_phrases:
  - "implementation"
  - "summary"
  - "template"
  - "impl summary core"
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
# Implementation Summary

<!-- SPECKIT_LEVEL: 2 -->
<!-- SPECKIT_TEMPLATE_SOURCE: impl-summary-core | v2.2 -->
<!-- HVR_REFERENCE: .opencode/skills/sk-doc/references/hvr_rules.md -->

---

<!-- ANCHOR:metadata -->
## Metadata

| Field | Value |
|-------|-------|
| **Spec Folder** | specs/034-vpn-status-hardening |
| **Completed** | 2026-10-04 |
| **Level** | 2 |
<!-- /ANCHOR:metadata -->

---

<!-- ANCHOR:what-built -->
## What Was Built

<!-- Voice guide:
     Open with a hook: what changed and why it matters. One paragraph, impact first.
     Then use ### subsections per feature. Each subsection: what it does + why it exists.
     Write "You can now inspect the trace" not "Trace inspection was implemented."
     NO "Files Changed" table for Level 3/3+. The narrative IS the summary.
     For Level 1-2, a Files Changed table after the narrative is fine.
     Reference: specs/system-spec-kit/020-mcp-working-memory-hybrid-rag/implementation-summary.md -->

После смены сервера VPN больше не убивает интернет на всей портативной: пикер конфигов получил bootstrap-резолвер (`domain_resolver: local`) и патч всех трёх режимных конфигов, heal перестал вычищать состояние прямо во время рестарта, а статус-панель остаётся честной и отзывчивой даже на мёртвом сервере (bounded-пробы вместо таймаут-шторма).

### Что теперь работает

Смена сервера в рантайме доводит туннель до CONNECTED за 3–6 с и больше не роняет DNS — можно переключать серверы прямо из QAM. Панель показывает намерение (вкл/выкл) стабильно, а фактическое состояние — в строке статуса. Все внешние пробы статуса ограничены по времени: мёртвый сервер даёт честный FAILED за ~8 с вместо «status failed» каждые 5 секунд.

### Files Changed

<!-- Include for Level 1-2. Omit for Level 3/3+ where the narrative carries. -->

| File | Action | Purpose |
|------|--------|---------|
| scripts/singbox-toggle.sh | Modified | bounds всех внешних проб status-json; heal→маркер порядок |
| scripts/singbox-server.sh | Modified | domain_resolver bootstrap + config-proxy + маркер перед рестартами |
| scripts/neodon-heal.sh | Modified | restart-guard (маркер + auto-restart) |
| decky/neodon-vpn/src/index.tsx | Modified | тумблер = intent; таймер не взводится на FAILED/LOCKED |
| decky/neodon-vpn/main.py | Modified | get_status timeout 15→30 с |
| decky/neodon-vpn/dist/index.js | Rebuilt | бандл панели (rollup) |
<!-- /ANCHOR:what-built -->

---

<!-- ANCHOR:how-delivered -->
## How It Was Delivered

<!-- Voice guide:
     Tell the delivery story. What gave you confidence this works?
     "All features shipped behind feature flags" not "Feature flags were used."
     For Level 1: a single sentence is enough.
     For Level 3+: describe stages (testing, rollout, verification). -->

Проверено живьём на устройстве (SSH, Game Mode): off→smart→CONNECTED (PL, 6 с), смена на NL — 3 с, обратно PL — 6 с; `.mode` стабилен; магазин Decky отдаёт каталог, YouTube 200. Bounded-прогон на мёртвом сервере #4: статус ~8 с, rc=0. Гейт `validate.sh --strict` PASSED. Поставлено SFTP-деплоем с бэкапами (.bak-20261004) и рестартом plugin_loader.
<!-- /ANCHOR:how-delivered -->

---

<!-- ANCHOR:decisions -->
## Key Decisions

<!-- Voice guide: "Why" column should read like you're explaining to a colleague.
     "Chose X because Y" not "X was selected due to Y." -->

| Decision | Why |
|----------|-----|
| Тумблер = intent (`desired_mode`), не actual | Флип по транзитным состояниям заставлял Steam пере-испускать onChange — фантомные vpn_up/down и реконнект-цикл |
| `domain_resolver: local` чинить в пикере, а не только в генераторе | Пикер заменяет outbound целиком; забытое поле = DNS-петля после любой смены сервера |
| heal-guard по маркеру `.transitioning` | ExecStopPost стреляет при каждом рестарте; guard отличает «переключение в полёте» от «туннель умер» |
<!-- /ANCHOR:decisions -->

---

<!-- ANCHOR:verification -->
## Verification

<!-- Voice guide: Be honest. Show failures alongside passes.
     "FAIL, TS2349 error in benchmarks.ts" not "Minor issues detected." -->

| Check | Result |
|-------|--------|
| bash -n / py_compile всех правленых скриптов | PASS |
| Живой цикл + switch NL/PL | PASS (3–6 с, .mode стабилен) |
| Dead-server bounded | PASS (~8 с, rc=0) |
| validate.sh --strict | PASSED (Errors 0 / Warnings 0) |
<!-- /ANCHOR:verification -->

---

<!-- ANCHOR:limitations -->
## Known Limitations

<!-- Voice guide: Number them. Be specific and actionable.
     "Adaptive fusion is enabled by default. Set SPECKIT_ADAPTIVE_FUSION=false to disable."
     not "Some features may require configuration."
     Write "None identified." if nothing applies. -->

1. **Мёртвые серверы провайдера** [4]DE/[5]FI/[9]US не отвечают с этой сети — не наш дефект; список рабочих см. CHANGES (ПL/NL/SW/AT/IS).
2. **`ipify`-латентность в статусе** включает первый коннект, не только RTT.
3. **Full-режим** не перегонялся в этом прогоне (правки его не касаются, smoke не гонялся).
<!-- /ANCHOR:limitations -->

---

<!--
CORE TEMPLATE: Post-implementation documentation, created AFTER work completes.
Write in human voice: active, direct, specific. No em dashes, no hedging, no AI filler.
HVR rules: .opencode/skills/sk-doc/references/hvr_rules.md
-->