---
title: "Починить VPN после апгрейда пакета (caps+se [spec:032-vpn-caps-and-compact-ui]"
description: "Починить VPN после апгрейда пакета (caps+sentinel) и сжать GUI под 7-дюймовый экран при scale 2.1; свести расхождения repo vs live host"
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
    packet_pointer: "specs/032-vpn-caps-and-compact-ui"
    last_updated_at: "2026-09-27T19:05:00Z"
    last_updated_by: "hermes-main"
    recent_action: "spec.md filled"
    next_safe_action: "Fill plan.md + tasks.md, run implementation"
    blockers: []
    key_files: ["tests/app/neodon-vpn.py", "hooks/90-neodon-sing-box-caps.hook", "install.sh", "release/stage.sh", "scripts/singbox-toggle.sh"]
    session_dedup:
      fingerprint: "sha256:bf51de0957ed0290fa16eb69ca727a6a807facfbebfbbd08d9cd025c1ada5667"
      session_id: "main-20260927"
      parent_session_id: null
    completion_pct: 15
    open_questions: []
    answered_questions: []
---
# Feature Specification: VPN caps self-heal + compact GUI (CachyOS Ally X)

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
| **Created** | 2026-09-27 |
| **Branch** | `032-vpn-caps-and-compact-ui` |
<!-- /ANCHOR:metadata -->

---

<!-- ANCHOR:problem -->
## 2. PROBLEM & PURPOSE

### Problem Statement
1) Сегодня 18:33 пакет `sing-box` обновился 1.14.1-2 → 1.14.2-1.1: pacman заменил `/usr/bin/sing-box`, file capabilities `cap_net_admin,cap_net_raw=ep` слетели. Все режимы с TUN (smart/full, десктоп и игровой режим) ушли в рестарт-луп: `FATAL start inbound/tun[tun-in]: TUNSETIFF: operation not permitted` (счётчик >1000); «ни к одному серверу не подключиться». Пользователь видел это и в десктопе, и в игровом режиме («закрыл панель — VPN мёртв»).
2) GUI-приложение (PySide6) на 7" 1080p при системном scale 2.1 (логический холст 914×514) громоздкое: окно 700×440, контент не влезает — список серверов срезан до «полоски», элементы крупные.
3) Репо и live-хост разошлись (QSS-размеры, settle-логика клика режима, `.full-since`, `SB` fallback) — релизы могут уехать с другим UI, чем работает на устройстве.

### Purpose
VPN работает сразу после любых обновлений пакета (caps самовосстанавливаются), GUI компактен и влезает в экран, репо = деплой (единый источник).
<!-- /ANCHOR:problem -->

---

<!-- ANCHOR:scope -->
## 3. SCOPE

### In Scope
- pacman hook `90-neodon-sing-box-caps.hook` (установлен на хост; добавить в репо + в installer + stage)
- Компактный UI-пасс GUI (QSS + фиксированные размеры + дефолт окна) под 914×514 logical
- Reconcile repo↔live: GUI (хост-версия как база), `.full-since` в toggle, `SB` fallback в server.sh
- CHANGES.md + GitHub commit (правило M501); обновление скилла bazzite-neodon-vpn

### Out of Scope
- Выпуск релиза/тэга — почему: не просили, релиз делается отдельно
- Смена системного масштаба KDE — почему: пользователь просил подстроить приложение под текущий масштаб, не наоборот
- Decky QAM-панель — почему: компоненты Steam-стиля, размеры задаёт Steam
- Деструктивные тесты killswitch/full — почему: туннель держать не нужно, guard оттестирован ранее

### Files to Change

| File Path | Change Type | Description |
|-----------|-------------|-------------|
| `tests/app/neodon-vpn.py` + `neodon-vpn.py` | Modify | компактный UI-пасс (база = live-версия), синхронно два экземпляра |
| `hooks/90-neodon-sing-box-caps.hook` | Create | pacman PostTransaction hook: setcap на sing-box при install/upgrade |
| `install.sh` | Modify | установка hook (Arch) + сообщение; без хардкода путей |
| `release/stage.sh` | Modify | включить hooks/ в tarball |
| `scripts/singbox-toggle.sh` | Modify | `.full-since` при старте full (порт с live; нужен guard'у) |
| `CHANGES.md` | Modify | запись 2026-09-27 (56) |
<!-- /ANCHOR:scope -->

---

<!-- ANCHOR:requirements -->
## 4. REQUIREMENTS

### P0 - Blockers (MUST complete)

| ID | Requirement | Acceptance Criteria |
|----|-------------|---------------------|
| REQ-001 | Caps самовосстанавливаются после апгрейда/переустановки пакета sing-box | `pacman -S sing-box` → hooks run показывает `Neodon VPN: restore cap_net_admin…`, `getcap /usr/bin/sing-box` = `ep`, TUN поднимается (доказано на живом хосте) |
| REQ-002 | Smart-режим подключается на живом хосте после фикса | `status-json` = CONNECTED, tun0 up, exit IP ≠ домашнего (94.183.209.x) |
| REQ-003 | GUI влезает в 914×514 logical без обрезки ключевого контента | grab-скриншот: видно ≥4 строк серверов, ничего не срезано, окно ≤ доступной геометрии |
| REQ-004 | repo = live после деплоя | md5 neodon-vpn.py repo == host; toggle/server.sh синхронизированы |
| REQ-005 | Hook поставляется installer'ом и release tarball'ом | `install.sh --dry-run` печатает шаг hook; в tarball есть `hooks/90-neodon-sing-box-caps.hook` |
| REQ-006 | Изменения зафиксированы | CHANGES.md запись + GitHub commit (API push) |

### P1 - Required (complete OR user-approved deferral)

| ID | Requirement | Acceptance Criteria |
|----|-------------|---------------------|
| REQ-007 | QA-сьют остаётся зелёным | `bash qa/run-all.sh --static` без новых FAIL |
| REQ-008 | Скилл обновлён (pitfall caps + hook + «панель не глушит VPN») | skill bazzite-neodon-vpn содержит pitfall |
<!-- /ANCHOR:requirements -->

---

<!-- ANCHOR:success-criteria -->
## 5. SUCCESS CRITERIA

- **SC-001**: После `pacman -S sing-box` VPN поднимается без ручных действий (hook отработал).
- **SC-002**: На экране устройства GUI выглядит компактно: список серверов виден в окне.
- **SC-003**: Репо-источник совпадает с деплоем → следующий релиз не откатит UI.
<!-- /ANCHOR:success-criteria -->

---

<!-- ANCHOR:risks -->
## 6. RISKS & DEPENDENCIES

| Type | Item | Impact | Mitigation |
|------|------|--------|------------|
| Dependency | pacman на хосте | Hook не отработает | Проверено живым reinstall'ом пакета |
| Risk | Компактный UI ломает тач-эргономику | Med | Интерактивные цели ≥ ~26 logical px (~55 физ.); проверка скриншотом |
| Risk | Рестарт GUI прервёт текущее состояние | Low | Бэкап файла + рестарт GUI; сервис VPN не трогается |
| Risk | Hook ставит caps на путь пакета | Low | Arch: /usr/bin/sing-box; installer симлинкует /usr/local/bin |
<!-- /ANCHOR:risks -->

---

<!-- ANCHOR:questions -->

---

<!-- ANCHOR:nfr -->
## L2: NON-FUNCTIONAL REQUIREMENTS

### Performance
- **NFR-P01**: UI-пасс не меняет логику опроса/сети (poll 8s, transitions log) — только геометрия/размеры.
- **NFR-P02**: grab-скриншот окна < 3 c (QA-хук уже есть).

### Security
- **NFR-S01**: Hook выполняется от root через pacman PostTransaction, команда фиксированная (без интерполяции).
- **NFR-S02**: Секреты/подписка не попадают в отчёт/логи.

### Reliability
- **NFR-R01**: После апгрейда пакета VPN восстанавливается без вмешательства (проверено reinstall'ом).
- **NFR-R02**: `.mode`/юниты остаются единственным источником правды для режима.
<!-- /ANCHOR:nfr -->

---

<!-- ANCHOR:edge-cases -->
## L2: EDGE CASES

### Data Boundaries
- Пустой `raw.json`: UI показывает 0 серверов, не падает (существующее поведение).
- Сохранённая геометрия окна 700×440 остаётся валидной (умещается).

### Error Scenarios
- Пакет sing-box поставится в другой путь: hook ставит caps на `/usr/bin/sing-box` (путь пакета Arch/CachyOS).
- GUI уже запущен: деплой + kill + рестарт с session-env (single-instance flock освобождается).

### State Transitions
- Режим full: toggle пишет `.full-since` (guard 30 мин → smart).
<!-- /ANCHOR:edge-cases -->

---

<!-- ANCHOR:complexity -->
## L2: COMPLEXITY ASSESSMENT

| Dimension | Score | Notes |
|-----------|-------|-------|
| Scope | 12/25 | 6 файлов + хост-деплой + скилл |
| Risk | 8/25 | TUN/caps — критично, но фикс проверен; UI — низкий риск |
| Research | 4/20 | Причина найдена по логам/пакетам, ресёрч не нужен |
| **Total** | **24/70** | **Level 2** |
<!-- /ANCHOR:complexity -->

---

## 10. OPEN QUESTIONS

- Нет блокирующих; улучшения (ресёрч) — отдельным списком после фикса.
<!-- /ANCHOR:questions -->
