---
title: "Починить VPN после апгрейда пакета (caps+se [spec:032-vpn-caps-and-compact-ui]"
description: "Починить VPN после апгрейда пакета (caps+sentinel) и сжать GUI под 7-дюймовый экран при scale 2.1; свести расхождения repo vs live host"
trigger_phrases:
  - "tasks"
  - "name"
  - "template"
  - "tasks core"
importance_tier: "normal"
contextType: "general"
_memory:
  continuity:
    packet_pointer: "specs/032-vpn-caps-and-compact-ui"
    last_updated_at: "2026-09-27T19:05:00Z"
    last_updated_by: "hermes-main"
    recent_action: "tasks.md filled"
    next_safe_action: "Execute tasks"
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
# Tasks: VPN caps self-heal + compact GUI (CachyOS Ally X)

<!-- SPECKIT_LEVEL: 2 -->
<!-- SPECKIT_TEMPLATE_SOURCE: tasks-core | v2.2 -->

---

<!-- ANCHOR:notation -->
## Task Notation

| Prefix | Meaning |
|--------|---------|
| `[ ]` | Pending |
| `[x]` | Completed |
| `[P]` | Parallelizable |
| `[B]` | Blocked |

**Task Format**: `T### [P?] Description (file path)`
<!-- /ANCHOR:notation -->

---

<!-- ANCHOR:phase-1 -->
## Phase 1: Setup

- [x] T001 Найти причину: journal sing-box restart-loop `TUNSETIFF: operation not permitted` / pacman.log upgrade 18:33 / `getcap` пуст (host 192.168.3.2)
- [x] T002 Немедленный фикс: `setcap cap_net_admin,cap_net_raw=ep /usr/bin/sing-box` → сервис живой, CONNECTED (exit 94.183.209.99)
- [x] T003 Спек-папка 032 создана (spec-new), план/таски заполнены
<!-- /ANCHOR:phase-1 -->

---

<!-- ANCHOR:phase-2 -->
## Phase 2: Implementation

- [x] T004 [P] Hook `90-neodon-sing-box-caps.hook` установлен на живой хост; доказан: `pacman -S --noconfirm sing-box` → «(5/8) Neodon VPN: restore cap_net_admin…» + `getcap` = `ep`
- [x] T005 [P] Hook → репо (`hooks/90-neodon-sing-box-caps.hook`) + `release/stage.sh` (include) + `install.sh` (установка на Arch, сообщение в вывод)
- [x] T006 [P] `.full-since` в `scripts/singbox-toggle.sh` (порт с live — нужен tunnel-guard'у)
- [x] T007 Компактный UI-пасс `tests/app/neodon-vpn.py` + root-копия: QSS (12px body, timer 20, h1 14), power 64→54, mode 34→28, sidebar 58→46, отступы/спейсинги, окно 700×660→820×620, min 420×380; серверные строки компактнее
- [x] T008 Деплой на хост: backup `.bak-20260927`, `install -m644`, рестарт GUI (session env), server.sh с `SB` fallback → хост
- [x] T009 CHANGES.md: запись (56) 2026-09-27
<!-- /ANCHOR:phase-2 -->

---

<!-- ANCHOR:phase-3 -->
## Phase 3: Verification

- [x] T010 grab-скриншот окна → vision: компактно, список серверов виден, ничего не срезано
- [x] T011 Live: `status-json` CONNECTED после рестарта GUI; transitions.log успокоился
- [x] T012 `qa/run-all.sh --static` без новых FAIL; `validate.sh --strict` PASS
- [x] T013 md5 repo == host (neodon-vpn.py); toggle/server.sh синхронизированы
- [ ] T014 GitHub commit (push_via_api.py); скилл bazzite-neodon-vpn обновлён
<!-- /ANCHOR:phase-3 -->

---

<!-- ANCHOR:completion -->
## Completion Criteria

- [ ] All tasks marked `[x]`
- [ ] No `[B]` blocked tasks remaining
- [ ] Manual verification passed
<!-- /ANCHOR:completion -->

---

<!-- ANCHOR:cross-refs -->
## Cross-References

- **Specification**: See `spec.md`
- **Plan**: See `plan.md`
<!-- /ANCHOR:cross-refs -->
