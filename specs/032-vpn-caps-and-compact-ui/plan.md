---
title: "Починить VPN после апгрейда пакета (caps+se [spec:032-vpn-caps-and-compact-ui]"
description: "Починить VPN после апгрейда пакета (caps+sentinel) и сжать GUI под 7-дюймовый экран при scale 2.1; свести расхождения repo vs live host"
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
    packet_pointer: "specs/032-vpn-caps-and-compact-ui"
    last_updated_at: "2026-09-27T19:05:00Z"
    last_updated_by: "hermes-main"
    recent_action: "plan.md filled"
    next_safe_action: "Fill tasks.md, implement"
    blockers: []
    key_files: ["tests/app/neodon-vpn.py", "hooks/90-neodon-sing-box-caps.hook", "install.sh", "release/stage.sh", "scripts/singbox-toggle.sh"]
    session_dedup:
      fingerprint: "sha256:bf51de0957ed0290fa16eb69ca727a6a807facfbebfbbd08d9cd025c1ada5667"
      session_id: "main-20260927"
      parent_session_id: null
    completion_pct: 25
    open_questions: []
    answered_questions: []
---
# Implementation Plan: VPN caps self-heal + compact GUI (CachyOS Ally X)

<!-- SPECKIT_LEVEL: 2 -->
<!-- SPECKIT_TEMPLATE_SOURCE: plan-core | v2.2 -->

---

<!-- ANCHOR:summary -->
## 1. SUMMARY

### Technical Context

| Aspect | Value |
|--------|-------|
| **Language/Stack** | Bash (systemd user units, pacman hooks), Python 3 + PySide6 (GUI), decky-плагин (TS/React, не трогаем) |
| **Framework** | sing-box 1.14.2 (TUN + mixed inbound), systemd --user |
| **Storage** | файлы `~/AI/singbox/*`, `~/AI/neodon-sub/raw.json` |
| **Testing** | qa/run-all.sh (static), grab-скриншот + vision, live status-json |

### Overview
Корень поломки — file capabilities на бинаре sing-box слетают при каждом апгрейде pacman-пакета; лечим не симптом, а класс — pacman PostTransaction hook сам переставляет `setcap` (идемпотентный). Второй трек — компактный UI-пасс GUI (размеры/шрифты/отступы), чтобы всё влезало в 914×514 logical при scale 2.1. Третий — свести repo↔live (единый источник), чтобы релиз не разъехался с деплоем.
<!-- /ANCHOR:summary -->

---

<!-- ANCHOR:quality-gates -->
## 2. QUALITY GATES

### Definition of Ready
- [x] Problem statement clear and scope documented
- [x] Success criteria measurable
- [x] Dependencies identified

### Definition of Done
- [ ] All acceptance criteria met
- [ ] Tests passing (if applicable)
- [ ] Docs updated (spec/plan/tasks)
<!-- /ANCHOR:quality-gates -->

---

<!-- ANCHOR:architecture -->
## 3. ARCHITECTURE

### Pattern
Monolith: тонкие UI (PySide6 GUI / Decky-панель) → общий bash-бэкенд (`singbox-toggle.sh`/`singbox-server.sh`) → systemd --user юниты sing-box.

### Key Components
- **singbox-toggle.sh**: единственная точка смены режима (smart/full/proxy/off), flock-мьютекс.
- **systemd --user sing-box.service**: smart-режим (TUN + mixed 10808).
- **pacman hook**: PostTransaction на пакет sing-box → `setcap cap_net_admin,cap_net_raw=ep /usr/bin/sing-box` (root, фиксированная команда).
- **neodon-vpn.py (GUI)**: UI-слой; размеры/шрифты — QSS + фиксированные размеры; grab-хук для QA-скриншотов.

### Data Flow
pacman upgrade → hook → setcap на свежий бинарь → `toggle smart` стартует юнит → sing-box открывает /dev/net/tun (caps) → трафик.
GUI: poll `toggle status-json` каждые 8с → состояние/exit IP.
<!-- /ANCHOR:architecture -->

---

<!-- ANCHOR:affected-surfaces -->
## FIX ADDENDUM: AFFECTED SURFACES

| Surface | Current Role | Action | Verification |
|---------|--------------|--------|--------------|
| `/usr/bin/sing-box` (пакет) | носитель caps | caps переставляет hook после каждого install/upgrade | `getcap` = ep после `pacman -S sing-box` |
| `install.sh` (установщик) | ставит caps один раз при установке | + установка hook (Arch) | `--dry-run` печатает шаг; на живом хосте repeat работал |
| `release/stage.sh` | собирает tarball | include `hooks/` | `tar -tzf` содержит hook |
| `scripts/singbox-toggle.sh` | режимы | + `.full-since` (guard) | grep строки; guard-скрипт читает её |
| `tests/app/neodon-vpn.py` | GUI (источник релиза) | компактный UI-пасс | grab+vision, QA static |
| `neodon-vpn.py` (root-копия) | дубль источника | синхронизировать | md5 равны |

Required inventories (выполнено):
- Same-class producers: `grep -n 'setcap' install.sh scripts/*.sh` — только installer.
- Consumers: `grep -n 'full-since' scripts/*.sh` — guard + toggle.
- Matrix axes: режим (smart/full/proxy/off) × носитель перезапуска (pacman upgrade / ручной setcap) — покрыт reinstall-тестом.
- Algorithm invariant: после ЛЮБОГО изменения файла `/usr/bin/sing-box` у него должны быть `cap_net_admin,cap_net_raw=ep` (adversarial: апгрейд, downgrade, reinstall).
<!-- /ANCHOR:affected-surfaces -->

---

<!-- ANCHOR:phases -->
## 4. IMPLEMENTATION PHASES

### Phase 1: Setup
- [x] Спек-папка 032 создана; хосты/пути разведаны (live = 192.168.3.2, m26)
- [x] Причина найдена: pacman.log 18:33 upgrade → getcap пуст → TUNSETIFF EPERM
- [x] Немедленный фикс применён на живом хосте (setcap) — VPN поднялся

### Phase 2: Core Implementation
- [x] hook установлен на хост + доказан reinstall'ом пакета (hooks run + getcap ep)
- [ ] hook + installer-шаг + stage в репо
- [ ] компактный UI-пасс GUI (база = live-версия) + deploy на хост
- [ ] reconcile: `.full-since` в repo-toggle; `SB` fallback → host
- [ ] CHANGES.md + commit

### Phase 3: Verification
- [ ] grab-скриншот компактного UI (vision) — список серверов виден
- [ ] live: smart CONNECTED + exit IP; GUI не ретраит после рестарта
- [ ] QA static suite без новых FAIL; validate.sh --strict PASS
- [ ] md5 repo == host (GUI)
<!-- /ANCHOR:phases -->

---

<!-- ANCHOR:testing -->
## 5. TESTING STRATEGY

| Test Type | Scope | Tools |
|-----------|-------|-------|
| Unit | hook-файл (синтаксис/идемпотентность) | `pacman -S --noconfirm sing-box` (живой reinstall) |
| Integration | toggle smart/full/proxy на хосте | `singbox-toggle.sh status-json`, `ip`, `curl` |
| Manual | GUI-масштаб | `grab`-хук → PNG → vision; QA `qa/run-all.sh --static` |
<!-- /ANCHOR:testing -->

---

<!-- ANCHOR:dependencies -->
## 6. DEPENDENCIES

| Dependency | Type | Status | Impact if Blocked |
|------------|------|--------|-------------------|
| pacman (Arch) | External | Green | без hook — ручной setcap после апгрейдов |
| CachyOS host 192.168.3.2 (m26) | External | Green | нет деплоя/проверки |
| GitHub API token (.env) | External | Green | без push — только локальный commit |
<!-- /ANCHOR:dependencies -->

---

<!-- ANCHOR:rollback -->
## 7. ROLLBACK PLAN

- **Trigger**: UI-пасс сломал взаимодействие или деплой не стартует.
- **Procedure**: `cp ~/AI/neodon-vpn/neodon-vpn.py.bak-<ts> ~/AI/neodon-vpn/neodon-vpn.py` + рестарт GUI; hook — `rm /etc/pacman.d/hooks/90-neodon-sing-box-caps.hook` (caps продолжат работать до следующего апгрейда пакета).
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
| Setup | Low | 0.5 ч (диагностика — сделано) |
| Core Implementation | Med | 1.5 ч |
| Verification | Low | 0.5 ч |
| **Total** | | **~2.5 ч** |
<!-- /ANCHOR:effort -->

---

<!-- ANCHOR:enhanced-rollback -->
## L2: ENHANCED ROLLBACK

### Pre-deployment Checklist
- [x] Backup создан (`.bak-<ts>` для GUI; hook — файл-одиночка)
- [x] Feature flag — не нужен (hook идемпотентен, UI — косметика)
- [x] Monitoring — transitions.log + journalctl (видно сразу)

### Rollback Procedure
1. `cp <bak> neodon-vpn.py` + рестарт GUI (режим VPN не затрагивается).
2. `rm /etc/pacman.d/hooks/90-neodon-sing-box-caps.hook`.
3. Проверка: `systemctl --user is-active sing-box` + `bash toggle status-json`.
4. Notify: пользователю — что откатили и почему.

### Data Reversal
- **Has data migrations?** No
- **Reversal procedure**: N/A
<!-- /ANCHOR:enhanced-rollback -->
