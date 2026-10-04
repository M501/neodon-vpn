---
title: "Neodon панель Decky: отзывчивое переключени [spec:035-panel-switch-ux]"
description: "Neodon панель Decky: отзывчивое переключение сервера и понятные статусы — мгновенный switching-индикатор, человеческие тексты вместо сырых FAILED/urlopen, ретрай повторного тапа по серверу, TTL transition-маркера 12с, ранняя запись selected-server.json"
trigger_phrases:
  - "implementation"
  - "summary"
  - "template"
  - "impl summary core"
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
# Implementation Summary

<!-- SPECKIT_LEVEL: 2 -->
<!-- SPECKIT_TEMPLATE_SOURCE: impl-summary-core | v2.2 -->
<!-- HVR_REFERENCE: .opencode/skills/sk-doc/references/hvr_rules.md -->

---

<!-- ANCHOR:metadata -->
## Metadata

| Field | Value |
|-------|-------|
| **Spec Folder** | specs/035-panel-switch-ux |
| **Completed** | 2026-10-04 |
| **Level** | 2 |
<!-- /ANCHOR:metadata -->

---

<!-- ANCHOR:what-built -->
## What Was Built

Панель Neodon в QAM больше не выглядит «залипшей» при смене сервера: клик сразу рисует «switching to X…», состояния говорят человеческим языком, а повторный тап по серверу честно повторяет попытку вместо молчаливого игнора.

### Отклик и статусы в панели

Ты выбираешь сервер — строка статуса в тот же тик показывает «● On (switching to PL…)», не дожидаясь пятисекундного полла. Дальше показывается фактический результат: «connected · 94.183.x» для живого сервера или «server not responding» + подсказка «pick another server, or tap this one again to retry» для мёртвого. Сырые строки (FAILED, urlopen-потроха) из UI убраны. Ошибки Refresh сжаты до «no network (DNS)» / «timeout» / «network error» и живут отдельной строкой, а не в скобках статуса.

### Ретрай и эхо

Повторный осознанный тап по тому же серверу отправляет свежий set_server (только если линк не CONNECTED); эхо Steam в пределах 800 мс после собственного обновления dropdown по-прежнему глушится. Ожидание переключения больше не держится слепым восьмисекундным окном: пока команда в полёте, дропдаун держит выбор пользователя, а подтверждение приходит по факту (selected == target и финальное состояние, максимум 15 с).

### Скрипты

Маркер `.transitioning` в status-json получил TTL 12 с вместо 30 (переключение занимает 2–6 с; долгий TRANSITIONING выглядел зависанием), heal-порог остался 35 с — строго больше. Пикер теперь пишет `selected-server.json` до рестарта сервиса: панель и статус видят новый выбор сразу.

### Files Changed

| File | Action | Purpose |
|------|--------|---------|
| decky/neodon-vpn/src/index.tsx | Modified | pending-индикация, friendly-статусы, ретрай-тап, shortErr, notice-строка |
| decky/neodon-vpn/dist/index.js (+ .map) | Rebuilt | бандл панели (rollup) |
| scripts/singbox-toggle.sh | Modified | TTL маркера .transitioning 30→12 с |
| scripts/singbox-server.sh | Modified | selected-server.json до рестарта сервиса |
| singbox-toggle.sh, singbox-server.sh (repo root) | Modified | синк репо-копий |
| CHANGES.md | Modified | запись итерации |
<!-- /ANCHOR:what-built -->

---

<!-- ANCHOR:how-delivered -->
## How It Was Delivered

Правки сделаны в репо, бандл собран rollup локально, файлы залиты на устройство SFTP с бэкапами (`.bak-20261004`), md5 сверен, plugin_loader перезапущен. Живой прогон на устройстве: переключение на живой сервер (PL), на мёртвый (DE) с наблюдением TRANSITIONING ≤12 с → DEGRADED, повторный set_server как ретрай; проверка магазина Decky при живом туннеле. Журнал plugin_loader использован как приёмка RPC-потока.
<!-- /ANCHOR:how-delivered -->

---

<!-- ANCHOR:decisions -->
## Key Decisions

| Decision | Why |
|----------|-----|
| Pending-модель вместо слепых quiet-окон | Окно 8 с было угадайкой: не покрывало медленные рестарты и глушило повторные тапы; pending снимается по факту подтверждения |
| Эхо-окно 800 мс вместо «любой same-value = эхо» | Осознанный повторный тап по мёртвому серверу должен работать (жалоба владельца «только если повторно нажмёшь на другой») |
| CONNECTED первого полла не принимается как финал (<3 с) | Иначе сразу после тапа показывался старый живой линк и pending снимался до реального переключения |
| TTL маркера 12 с, heal-порог не тронут (35 с) | TTL больше не завышается (30 с читались как зависание); heal-guard остаётся строго больше TTL |
| Запись selected до рестарта | Панель/статус/десктоп читают этот файл; поздняя запись давала «старый сервер» в UI |
<!-- /ANCHOR:decisions -->

---

<!-- ANCHOR:verification -->
## Verification

| Check | Result |
|-------|--------|
| rollup build (node 26, Windows) | PASS |
| bash -n scripts/singbox-toggle.sh, singbox-server.sh | PASS |
| Живой прогон: OFF→set(PL) 0.33 с; smart→CONNECTED (94.183.209.111); магазин/YouTube 200; DE: TRANSITIONING→DEGRADED по TTL 12 с; обратно PL 4 с | PASS |
| journal plugin_loader: плагин перезапущен, backend up, фантомов в прогоне нет (пары ретрай-тапа — на приёмке владельца) | PASS |
| validate.sh --strict | PASSED |
<!-- /ANCHOR:verification -->

---

<!-- ANCHOR:limitations -->
## Known Limitations

1. **Живость серверов панель не знает** — список не показывает «мёртвый/живой»; это отдельная фича (пробы по всем серверам).
2. **Watchdog по-прежнему выключает VPN при мёртвом туннеле** (internet-first) — это осознанное поведение, панель просто честнее объясняет состояние.
3. **Usage** сверяется с внешним устройством владельца отдельно от этой спеки.
<!-- /ANCHOR:limitations -->
