---
title: "NeodonVpn GUI: иконка в таскбаре KDE — привяза [spec:037-gui-taskbar-icon]"
description: "Итог: setDesktopFileName(\"io.neodon.gui\") добавлен в main() GUI; app_id окна в KWin изменился python3 → io.neodon.gui; в таскбаре жёлтая W (fallback wayland) заменена на иконку приложения."
trigger_phrases:
  - "implementation"
  - "summary"
  - "setDesktopFileName"
  - "taskbar icon"
importance_tier: "normal"
contextType: "general"
_memory:
  continuity:
    packet_pointer: "specs/037-gui-taskbar-icon"
    last_updated_at: "2026-10-05T02:27:16Z"
    last_updated_by: "hermes-main"
    recent_action: "Spec folder created"
    next_safe_action: "Fill spec.md"
    blockers: []
    key_files: []
    session_dedup:
      fingerprint: "sha256:2e547ada75cd63804b9d043483d981bc2d68adc599538ce4ee35a74e43730ab2"
      session_id: "main-20261005"
      parent_session_id: null
    completion_pct: 0
    open_questions: []
    answered_questions: []
---
# Implementation Summary

<!-- SPECKIT_LEVEL: 1 -->
<!-- SPECKIT_TEMPLATE_SOURCE: impl-summary-core | v2.2 -->
<!-- HVR_REFERENCE: .opencode/skills/sk-doc/references/hvr_rules.md -->

---

<!-- ANCHOR:metadata -->
## Metadata

| Field | Value |
|-------|-------|
| **Spec Folder** | 037-gui-taskbar-icon |
| **Completed** | 2026-10-05 |
| **Level** | 1 |
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

Окно Neodon VPN перестало быть «безымянным» для KDE: теперь таскбар, переключатель окон и Alt-Tab берут его иконку из `io.neodon.gui.desktop` — ту же, что на рабочем столе и в меню.

Раньше окно несло app_id `python3` (Qt Wayland брал имя интерпретатора, потому что GUI не заявлял desktop-файл), KWin не находил `python3.desktop` и рисовал fallback-иконку темы Breeze `wayland.svg` — «жёлтую W», на которую и пожаловался владелец. Фикс — одна строка в `main()` сразу после создания `QApplication`: окно привязывается к desktop-файлу `io.neodon.gui`.

### Files Changed

| File | Action | Purpose |
|------|--------|---------|
| `/home/m26/AI/neodon-vpn/neodon-vpn.py` (live) | Modified | +2 строки (комментарий + `setDesktopFileName`) |
| `neodon-vpn.py` (repo) | Modified | Синхронная копия (md5 ×3 идентичен) |
| `tests/app/neodon-vpn.py` | Modified | Копия для stage.sh — синхронна |
| `CHANGES.md` | Modified | Запись 2026-10-05 (66) с пруфами |
| `specs/037-gui-taskbar-icon/` | Created | Спека + план + tasks + summary |
<!-- /ANCHOR:what-built -->

---

<!-- ANCHOR:how-delivered -->
## How It Was Delivered

<!-- Voice guide:
     Tell the delivery story. What gave you confidence this works?
     "All features shipped behind feature flags" not "Feature flags were used."
     For Level 1: a single sentence is enough.
     For Level 3+: describe stages (testing, rollout, verification). -->

Диагноз доказан живьём до правки: KWin-скриптом через D-Bus — app_id `python3`; fallback-файл `/usr/share/icons/breeze/apps/48/wayland.svg` найден на диске; скриншот «до» снят и разобран по пикселям. После правки live-копия обновлена по SFTP (бэкап `/tmp/neodon-vpn.py.pre037`), GUI перезапущен через `systemd-run --user` (пережил закрытие SSH-канала), затем двойная верификация: KWin-скрипт показал `desktopFileName=io.neodon.gui`, а пиксельный разбор свежего скриншота — синий квадрат с белым щитом вместо жёлтой W. md5 всех трёх копий кода совпал.
<!-- /ANCHOR:how-delivered -->

---

<!-- ANCHOR:decisions -->
## Key Decisions

<!-- Voice guide: "Why" column should read like you're explaining to a colleague.
     "Chose X because Y" not "X was selected due to Y." -->

| Decision | Why |
|----------|-----|
| `setDesktopFileName` вместо правки `.desktop`-файлов | `.desktop` уже корректный (`Icon=io.neodon.gui`); не матчился сам app_id окна — чинить нужно на стороне приложения |
| Не трогать `StartupWMClass=neodon-vpn.py` | Остаётся X11-легаси; Wayland-путь работает через app_id, риск регрессии нулевой |
| Рестарт GUI через `systemd-run --user` | Проверенный путь из скилла: переживает закрытие SSH, не зависит от KDE-автозапуска |
| Клик по позиции кнопки не делался | Живое состояние читалось через KWin D-Bus и пиксель-разбор — без вмешательства в сессию владельца |
<!-- /ANCHOR:decisions -->

---

<!-- ANCHOR:verification -->
## Verification

<!-- Voice guide: Be honest. Show failures alongside passes.
     "FAIL, TS2349 error in benchmarks.ts" not "Minor issues detected." -->

| Check | Result |
|-------|--------|
| `python -m py_compile` обеих копий до деплоя | PASS |
| md5 live == repo == tests/app | PASS (`3d5938ce2b3d9248f01f90116731aa0d` ×3) |
| KWINDBG до правки | `python3 \| python3.14 \| python3 \| Neodon VPN \| 15775` (fallback) |
| KWINDBG после правки | `io.neodon.gui \| python3.14 \| io.neodon.gui \| Neodon VPN \| 26144` (PASS) |
| Пиксельный пруф «до» | жёлтая W (wayland.svg) на кнопке таскбара |
| Пиксельный пруф «после» | синий скруглённый квадрат с белым контуром-щитом (`#2b6cb0` из `io.neodon.gui.svg`) + индикатор активности |
| `validate.sh --strict` | PASSED |
<!-- /ANCHOR:verification -->

---

<!-- ANCHOR:limitations -->
## Known Limitations

<!-- Voice guide: Number them. Be specific and actionable.
     "Adaptive fusion is enabled by default. Set SPECKIT_ADAPTIVE_FUSION=false to disable."
     not "Some features may require configuration."
     Write "None identified." if nothing applies. -->

1. **X11-сессии не проверялись** — устройство живёт на Wayland; `StartupWMClass` сохранён для совместимости, но X11-путь не тестирован.
2. **Позиция кнопки в таскбаре сместилась** (следствие пересоздания окна; KDE ставит новые задачи в конец) — нормальное поведение, не дефект.
3. **CHANGES.md и правки доков — в рабочем дереве**: repo в момент работы оказался в состоянии незавершённого внешнего merge («reconcile M5/device series», started 05:36), коммит отложен до его завершения (tasks T012).
<!-- /ANCHOR:limitations -->

---

<!--
CORE TEMPLATE: Post-implementation documentation, created AFTER work completes.
Write in human voice: active, direct, specific. No em dashes, no hedging, no AI filler.
HVR rules: .opencode/skills/sk-doc/references/hvr_rules.md
-->