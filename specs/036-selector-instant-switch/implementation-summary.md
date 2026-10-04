---
title: "Selector instant switch [spec:036-selector-instant-switch]"
description: "Mini phase 1: selector + urltest + Clash API — мгновенное переключение сервера без рестарта"
trigger_phrases:
  - "implementation"
  - "summary"
importance_tier: "normal"
contextType: "general"
_memory:
  continuity:
    packet_pointer: "specs/036-selector-instant-switch"
    last_updated_at: "2026-10-04T06:00:00Z"
    last_updated_by: "hermes-main"
    recent_action: "Implemented + verified live"
    next_safe_action: "Owner acceptance"
    blockers: []
    key_files: []
    session_dedup:
      fingerprint: "sha256:66fe3c95194e019c99a60246f874f5ec63dae6209757940e62ccf55a49e2e7f7"
      session_id: "main-20261004"
      parent_session_id: null
    completion_pct: 95
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
| **Spec Folder** | specs/036-selector-instant-switch |
| **Completed** | 2026-10-04 |
| **Level** | 2 |
<!-- /ANCHOR:metadata -->

---

<!-- ANCHOR:what-built -->
## What Was Built

Смена сервера перестала быть «переездом»: теперь это переключение селектора sing-box через локальный Clash API — **0.1 секунды, без рестарта ядра, без маркеров, без TRANSITIONING**.

### Как это устроено

Живые конфиги получили все 12 нод (n0..n11), авто-группу `urltest` (`auto`, проба api.ipify.org каждые 60 с) и selector **с сохранённым тегом `proxy`** — поэтому правила маршрутизации, профили и DNS-цепочка не менялись вовсе. `singbox-server.sh set N` больше не патчит JSON и не рестартует сервис: он делает `PUT /proxies/proxy {"name":"nN"}` и сохраняет выбор (`.preferred-server` + `selected-server.json`). При включении VPN (toggle smart/full/proxy) `apply_pref` возвращает сохранённый выбор; `cache_file` держит его между рестартами. Killswitch для FULL теперь allowlist'ит IP всех нод. Панель: дропдаун серверов получил key-ремаунт (страховка от залипания отображения).

### Files Changed

| File | Action | Purpose |
|------|--------|---------|
| scripts/singbox-server.sh | Rewrite | PUT-переключение + персист + фоллбэки (0.1 с) |
| scripts/singbox-toggle.sh | Modified | apply_pref после старта (smart/full/proxy) |
| killswitch.sh (live) | Modified | allowlist всех 12 нод (FULL) |
| decky/neodon-vpn/src/index.tsx + dist | Modified | key-ремаунт дропдауна серверов |
| ~/AI/singbox/config*.json | Migrated | 12 нод + auto + selector(proxy) + clash_api + cache_file |
| migrate_selector.py (устройство, разовый) | Created | check-gated миграция с бэкапами |
<!-- /ANCHOR:what-built -->

---

<!-- ANCHOR:how-delivered -->
## How It Was Delivered

Миграция прогнана на устройстве с `sing-box check` на каждом кандидате и бэкапами `.pre-sel-20261004`; скрипты задеплоены с бэкапами `.bak-20261004-sel`, md5 сверены. Живой прогон: OFF→smart→CONNECTED за 4 с (apply_pref поставил n0), set 1 (NL) — 0.10 с / exit 203.188.180.46, set 0 (PL) — 0.09 с / exit 94.183.209.102; Clash API отдаёт now=nN. plugin_loader перезапущен, панель на новом бандле.
<!-- /ANCHOR:how-delivered -->

---

<!-- ANCHOR:decisions -->
## Key Decisions

| Decision | Why |
|----------|-----|
| Сохранить тег `proxy` за селектором | Нулевой дифф: route.rules/profiles/dns/final уже указывают на `proxy` — ничего не переписываем |
| .preferred-server + apply_pref (а не только cache_file) | Явное применение выбора после OFF→ON; cache — вторая страховка на рестарты |
| Фоллбэк: рестарт активного юнита только при молчащем API | Не трогаем норму; рестарт — редкий путь восстановления |
| killswitch: allowlist всех нод | FULL + auto-выбор не должен резать живые ноды fail-closed политикой |
<!-- /ANCHOR:decisions -->

---

<!-- ANCHOR:verification -->
## Verification

| Check | Result |
|-------|--------|
| sing-box check ×3 (миграция, tmp-gated) | PASS |
| bash -n toggle/server | PASS |
| set 1 / set 0 тайминги | 0.10 с / 0.09 с (было 10–20+ с) |
| exit_ip смена (NL/PL) | PASS (203.188.180.46 / 94.183.209.102) |
| Clash API | PASS (now/all) |
| md5 устройство==репо | PASS |
| FULL-прогон killswitch | не гонялся в этом прогоне (отмечено) |
<!-- /ANCHOR:verification -->

---

<!-- ANCHOR:limitations -->
## Known Limitations

1. **Авто-failover при смерти РУЧНОГО выбора** — фаза 2 (manager): сейчас мёртвый ручной сервер даст DEGRADED, пока владелец не выберет другой (теперь это 0.1 с).
2. **DNS по-прежнему через прокси** (deadlock при мёртвом сервере) — фаза 1b архитектуры.
3. **FULL-режим** с новой топологией не перегонялся живьём (killswitch обновлён, но smoke не гонялся).
<!-- /ANCHOR:limitations -->
