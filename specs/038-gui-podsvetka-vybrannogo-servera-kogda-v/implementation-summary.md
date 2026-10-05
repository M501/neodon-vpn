---
title: "NeodonVpn GUI: подсветка выбранного сервера + вертикальный [spec:038-gui-podsvetka-vybrannogo-servera-kogda-v]"
description: "Итог: выбранный сервер подсвечен при OFF (selected-server.json + Clash API), скролл только вертикальный (_VScroll), тап-гвард по позиции скроллбара."
trigger_phrases:
  - "implementation"
  - "summary"
  - "server highlight"
  - "vertical scroll"
importance_tier: "normal"
contextType: "general"
_memory:
  continuity:
    packet_pointer: "specs/038-gui-podsvetka-vybrannogo-servera-kogda-v"
    last_updated_at: "2026-10-05T21:05:00Z"
    last_updated_by: "hermes-main"
    recent_action: "implementation done, verified live, docs filled"
    next_safe_action: "commit and push"
    blockers: []
    key_files: ["neodon-vpn.py", "tests/app/neodon-vpn.py", "CHANGES.md"]
    session_dedup:
      fingerprint: "sha256:0d62fed10591cd75dd55ff7121bac1859a7b70ba1fb7b0250cbc5c211270aaa7"
      session_id: "main-20261005"
      parent_session_id: null
    completion_pct: 100
    open_questions: []
    answered_questions: []
---
# Implementation Summary

<!-- SPECKIT_LEVEL: 1 -->
<!-- SPECKIT_TEMPLATE_SOURCE: impl-summary-core | v2.2 -->

---

<!-- ANCHOR:metadata -->
## Metadata

| Field | Value |
|-------|-------|
| **Spec Folder** | 038-gui-podsvetka-vybrannogo-servera-kogda-v |
| **Completed** | 2026-10-05 |
| **Level** | 1 |
<!-- /ANCHOR:metadata -->

---

<!-- ANCHOR:what-built -->
## What Was Built

Владелец открывает десктопный GUI и сразу видит, какой сервер выбран — даже когда VPN выключен; тач-скролл больше не таскает интерфейс влево-вправо и не переключает серверы на ходу.

Раньше подсветки не было вообще: `render_servers()` определял «активный» сервер из `config.json` у аутбаунда `tag=proxy` по ключу `server`, а после selector-модели (спека 036) `proxy` — это `selector` без поля `server` во всех трёх конфигах, поэтому `active_addr` всегда оставался пустым. Теперь выбор берётся из `~/AI/singbox/selected-server.json` (тот же файл, что читают Decky-панель и `status-json`), а фактически применённая нода — из Clash API (`GET /proxies/proxy` → `now`).

У горизонтального движения контента было два источника, и оба закрыты: страница была шире вьюпорта (подпись карточки не эллизилась: 509 px против 498 px вьюпорта) — теперь подпись эллидится, а скролл-области стали `_VScroll` (содержимое никогда не шире вьюпорта, горизонтальный диапазон 0); плюс найден и убит дефект тап-логики, из-за которого прокрутка списка выбирала сервер под пальцем.

### Подсветка выбора

- Выбранная карточка — accent-рамка `#3373F7` и синий тон `#16203A`; фактически применённая нода — прежняя зелёная рамка плюс `●` в имени.
- Тап по карточке подсвечивает её мгновенно, не дожидаясь ответа бэкенда.
- Смена сервера из панели Decky переезжает в десктоп-GUI за один полл (≤8 с) — источник `status-json.server_tag`.
- Выбор сервера по-прежнему ничего не включает: power только тумблером.

### Скролл и тапы

- `_VScroll` + `ScrollBarAlwaysOff` + эллидящая подпись: минимальная ширина страницы home 509 → 260 px, горизонтальный диапазон 0 при 565/820/420.
- `_ClickFrame` не считает тапом ни отпуск без нажатия на этой карточке, ни отпуск при изменившейся позиции скроллбара. Замер, который это вскрыл: при тач-скролле карточка едет вместе с контентом, поэтому локальная дельта почти нулевая (`local 18→17` при `global 412→247`, скроллбар `0→164`).

### Files Changed

| File | Action | Purpose |
|------|--------|---------|
| `/home/m26/AI/neodon-vpn/neodon-vpn.py` (live) | Modified | Деплой правки на устройство (бэкап `neodon-vpn.py.pre038`) |
| `neodon-vpn.py` (repo) | Modified | Подсветка выбора, `selector_now()`, `_VScroll`, тап-гвард |
| `tests/app/neodon-vpn.py` | Modified | Синхронная копия для `stage.sh` (md5 совпадает) |
| `CHANGES.md` | Modified | Запись 2026-10-05 (67) с пруфами |
| `specs/038-gui-podsvetka-vybrannogo-servera-kogda-v/` | Created | Спека + план + tasks + summary + `scratch/` (скрипты и снимки проверки) |
<!-- /ANCHOR:what-built -->

---

<!-- ANCHOR:how-delivered -->
## How It Was Delivered

Сначала диагноз на живом устройстве, потом код: дамп аутбаундов `proxy`/`auto` во всех трёх конфигах доказал, что поле `server` исчезло; offscreen-проба геометрии назвала точные числа (`minHint 509` против `viewport 498`); синтетический палец через uinput показал реальный сдвиг контента; а инструментированная сборка (временный `neodon-vpn-dbg.py` на устройстве, мимо репозитория) дала точный замер события press/release, который объяснил выбор сервера при прокрутке. Правка внесена в репозиторий и в живую копию, GUI перезапущен через `systemd-run --user`, затем всё проверено его же данными: grab окна, разбор пикселей рамки, дифф снимков до/после свайпа. Диагностические скрипты и снимки лежат в `scratch/` — проверку можно повторить.
<!-- /ANCHOR:how-delivered -->

---

<!-- ANCHOR:decisions -->
## Key Decisions

| Decision | Why |
|----------|-----|
| Источник выбора — `selected-server.json`, а не `config.json` | Это тот же файл, что читают Decky-панель и `status-json`; только так все UI показывают один выбор, без второго источника истины |
| Живую ноду брать из Clash API | В selector-модели применённая нода живёт только в API (`now = n<idx>`), конфиг её не знает |
| Метка живой ноды — текст `●`, а не второй цвет рамки | Рамка занята выбором; смешивать два состояния в одном цвете — ровно тот дефект, из-за которого подсветка «исчезла» |
| Класс `_VScroll`, а не один `setHorizontalScrollBarPolicy` | Политика прячет полосу, но диапазон остаётся и QScroller всё равно тащит контент; ноль диапазона даёт только кламп ширины содержимого |
| Тап-гвард по позиции скроллбара, а не по времени нажатия | Время у тапа и короткого свайпа пересекается; факт движения страницы — однозначное доказательство скролла |
| Диагностика временной сборкой на устройстве | Слой тача (QScroller) не воспроизводится offscreen, а инструментировать репозиторий ради замера — лишний риск |
<!-- /ANCHOR:decisions -->

---

<!-- ANCHOR:verification -->
## Verification

| Check | Result |
|-------|--------|
| `python -m py_compile` обеих копий | PASS |
| md5 live == repo == tests/app | PASS (`7a10829db18101497a93c9386b2f00ba` ×3) |
| `hRange` на страницах при 565/820/420 | PASS — 0 везде; home `minHint 509 → 260` |
| Подсветка при OFF, внешние `set 2` / `set 1` | PASS — рамка LEFT row0 → LEFT row1 → RIGHT row0, возврат назад |
| Тап по карточке (uinput, 90 мс) | PASS — `selected-server.json` = индекс 3, рамка на ней; подтверждено независимым зрением по снимку `scratch/grabs/p_tap.png` |
| Вертикальный свайп по карточке | PASS — прокрутка есть (скроллбар 0 → 164), выбор не меняется |
| Горизонтальные свайпы в обе стороны | PASS — `dx = 0, dy = 0`, residual 0.000 |
| VPN ON (smart) | PASS — Clash API `now = n0`, рамка на n0, снимок `scratch/grabs/f_on.png` |
| Финальное состояние | PASS — `.mode = off`, юниты inactive, выбор владельца (индекс 0) восстановлен; автоподключения не было ни на одном шаге |
| `validate.sh --strict` | PASSED |
<!-- /ANCHOR:verification -->

---

<!-- ANCHOR:limitations -->
## Known Limitations

1. **Широкое содержимое теперь обрезается, а не прокручивается** — свойство выбранного решения: при окне уже 420 px элемент шире вьюпорта будет обрезан. Проверено на 420 px — обрезки нет; если появится, правильный путь — эллизить или переносить этот элемент, а не возвращать горизонтальный скролл.
2. **Живой маркер обновляется не мгновенно** — при включении VPN он ставится на переходе в CONNECTED; при `urltest auto` фактическая нода может смениться позже.
3. **Панель Decky не менялась** — она уже читает `selected-server.json`; выделение выбранного сервера в QAM осталось прежним (дропдаун), это отдельный UI.
4. **Побочная находка вне скоупа:** keeper сна (`remote-keeper` v4) блокирует только `idle`, поэтому PowerDevil усыпляет устройство через `sleep` — портативка уснула посреди работ. На время работ поднимался `hermes-sleep-hold.service` (`sleep:idle`, TTL 90 мин), снят по завершении; лечение keeper'а — отдельное решение владельца.
<!-- /ANCHOR:limitations -->

---

<!--
CORE TEMPLATE: Post-implementation documentation, created AFTER work completes.
Write in human voice: active, direct, specific.
-->
