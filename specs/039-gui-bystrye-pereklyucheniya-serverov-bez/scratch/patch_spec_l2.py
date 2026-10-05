"""Append the Level-2 addendum sections and write a filled checklist.md."""
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)) + "/..")

SPEC_ADD = """
---

<!-- ANCHOR:complexity -->
## L2: COMPLEXITY ASSESSMENT

| Aspect | Value |
|--------|-------|
| Файлов изменено | 3 (GUI в двух синхронных копиях, `scripts/singbox-toggle.sh`) + 1 новый ассет (`flags/DE.png`) |
| Удалено | 3 мёртвых скрипта-дубля, 2 мёртвых элемента UI, 2 мёртвых метода, дублирующий блок импортов |
| Новых сущностей | 3 (`_sel_intent`, `_paint_selection()`, `_LAST_TAP`) |
| Точка риска | правило второго тапа (свежесть + неподвижный скролл) |
| Обратимость | полная: `.pre038`/`.pre039` на устройстве и история git |
<!-- /ANCHOR:complexity -->

---

<!-- ANCHOR:nfr -->
## L2: NON-FUNCTIONAL REQUIREMENTS

| Category | Requirement | Verification |
|----------|-------------|--------------|
| Отзывчивость | тап даёт видимую подсветку, не дожидаясь бэкенда | снимок окна сразу после тапа |
| Отзывчивость | перерисовка выбора не пересоздаёт сетку (нет мигания) | `_paint_selection()` + бурст снимков |
| Надёжность | статус-полл не перебивает выбор пользователя | тест двойного тапа + внешний `set` |
| Безопасность | ссылка подписки не может испортить конвертер подписки | проверка `save_sub_url` на кавычки и переводы строк |
| Данные | одновременные refresh не перезаписывают `raw.json` половинчатым телом | флаг `_sub_busy` + имена временных файлов с PID |
| Честность интерфейса | `off` не рапортует «internet via ISP», пока REJECT на месте | живой прогон smart→off |
<!-- /ANCHOR:nfr -->

---

<!-- ANCHOR:edge-cases -->
## L2: EDGE CASES

| Case | Expected behavior | Verified |
|------|-------------------|----------|
| Два тапа по разным серверам с гэпом 150 мс | выбирается второй, подсветка не возвращается | да (4 кадра бурста) |
| Два тапа с гэпом 250 мс | то же | да |
| Тап при выключенном VPN | выбор сохраняется, VPN не включается | да |
| Протяжка вниз на самом верху списка (скролл не двигается) | выбора нет | да |
| Прокрутка списка пальцем | выбора нет, прокрутка работает | да |
| Горизонтальный свайп | контент не двигается, выбора нет | да |
| Смена сервера из Decky-панели | подсветка переезжает в пределах полла | да |
| Нет файла флага для страны | показывается код страны | да (DE до добавления ассета) |
| Два refresh подписки подряд | второй отклоняется, `raw.json` не портится | по коду + флаг `_sub_busy` |
<!-- /ANCHOR:edge-cases -->
"""

PLAN_ADD = """
---

<!-- ANCHOR:effort -->
## L2: EFFORT ESTIMATION

| Phase | Effort | Notes |
|-------|--------|-------|
| Диагностика (спай событий, гэпы, флаги) | ~1.5 ч | три измерительных прохода на устройстве |
| Правки GUI | ~1 ч | интент выбора, `_paint_selection`, тап-логика, ассет |
| Аудит и разбор находок | ~1.5 ч | три ревьюера + собственная проверка каждой находки |
| Фиксы аудита и control-plane | ~1 ч | 9 фиксов, включая честный `off` |
| Приёмка и документы | ~1 ч | синтетический тач, снимки, спека, CHANGES |
<!-- /ANCHOR:effort -->

---

<!-- ANCHOR:phase-deps -->
## L2: PHASE DEPENDENCIES

| Phase | Depends on | Blocks |
|-------|------------|--------|
| Диагностика | доступ к устройству и хуку снимков | правки (без измерений это было бы гадание) |
| Правки GUI | диагностика | приёмку |
| Аудит | читаемое состояние репозитория | фиксы аудита (правки GUI не блокирует) |
| Фиксы control-plane | подтверждение находки про `off` | живую проверку `off` |
| Приёмка | правки и деплой | коммит и релиз |
<!-- /ANCHOR:phase-deps -->

---

<!-- ANCHOR:enhanced-rollback -->
## L2: ENHANCED ROLLBACK

| Level | Action | Trigger |
|-------|--------|---------|
| GUI | вернуть `neodon-vpn.py.pre039` и перезапустить `neodon-gui-live.service` | тап не работает, подсветка врёт, окно не открывается |
| Репо | `git revert <commit>` либо `git checkout -- neodon-vpn.py tests/app/neodon-vpn.py` | регресс подтверждён тестом |
| Control-plane | вернуть `~/AI/singbox/singbox-toggle.sh.pre039` и выполнить `singbox-toggle.sh off` | `off` не снимает правила или печатает неправду |
| Ассет | удалить `flags/DE.png` (появится код страны) | флаг ломает вёрстку карточки |
| Данные | `selected-server.json` и `raw.json` этой волной не меняются | — |
<!-- /ANCHOR:enhanced-rollback -->
"""

CHECKLIST = """---
title: "Чек-лист 039: быстрые переключения, флаги, доводка [spec:039-gui-bystrye-pereklyucheniya-serverov-bez]"
description: "Приёмочный чек-лист волны 039"
trigger_phrases:
  - "checklist"
  - "acceptance"
  - "fast switching"
importance_tier: "normal"
contextType: "general"
_memory:
  continuity:
    packet_pointer: "specs/039-gui-bystrye-pereklyucheniya-serverov-bez"
    last_updated_at: "2026-10-05T22:00:00Z"
    last_updated_by: "hermes-main"
    recent_action: "checklist filled after the acceptance run"
    next_safe_action: "commit and push"
    blockers: []
    key_files: ["neodon-vpn.py", "flags/DE.png", "scripts/singbox-toggle.sh"]
    session_dedup:
      fingerprint: "sha256:0d62fed10591cd75dd55ff7121bac1859a7b70ba1fb7b0250cbc5c211270aaa7"
      session_id: "main-20261005"
      parent_session_id: "038-gui-podsvetka-vybrannogo-servera-kogda-v"
    completion_pct: 95
    open_questions: []
    answered_questions: []
---
# Checklist: быстрые переключения, флаги, доводка

<!-- SPECKIT_LEVEL: 2 -->
<!-- SPECKIT_TEMPLATE_SOURCE: checklist | v2.2 -->

---

<!-- ANCHOR:pre-impl -->
## Pre-Implementation

- [x] Жалоба владельца зафиксирована в spec.md
- [x] Корневые причины измерены на устройстве (лог карточек, спай событий, гэпы, пиксельная проверка флагов)
- [x] Бэкапы живой копии созданы до деплоя (`.pre039`)
- [x] Точки отката описаны (GUI, репо, control-plane, ассет)
<!-- /ANCHOR:pre-impl -->

---

<!-- ANCHOR:security -->
## Security

- [x] Ссылка подписки не может закрыть строку в конвертере (отказ на кавычки, бэкслеши, переводы строк)
- [x] Временные файлы refresh больше не фиксированные во `/tmp` (имена с PID)
- [x] Дочерние процессы не получили новых прав, `sudo` остаётся только `-n`
- [x] Секреты и токены не попадали в вывод и в файлы отчётов
<!-- /ANCHOR:security -->

---

<!-- ANCHOR:code-quality -->
## Code Quality

- [x] `python -m py_compile` на обеих копиях GUI — PASS
- [x] `bash -n` для правленого скрипта — PASS
- [x] Мёртвый код удалён, а не закомментирован
- [x] Комментарии объясняют WHY (замеры), без эфемерных меток спек
<!-- /ANCHOR:code-quality -->

---

<!-- ANCHOR:testing -->
## Testing

- [x] Одиночный тап выбирает сервер (контроль)
- [x] Двойной тап 150 мс: второй тап доходит, подсветка без прыжков
- [x] Двойной тап 250 мс: то же
- [x] Протяжка вниз при неподвижном скролле: выбора нет
- [x] Вертикальный свайп: прокрутка есть, выбора нет
- [x] Горизонтальные свайпы в обе стороны: сдвиг 0, выбора нет
- [x] Внешний `set N` (как из панели): подсветка переезжает
- [x] Флаг DE подтверждён пикселями карточки
- [x] Все страницы GUI открываются после удаления мёртвого UI
- [x] Честный `off`: 0 правил prio 20, интернет через провайдера, юниты inactive
<!-- /ANCHOR:testing -->

---

<!-- ANCHOR:file-org -->
## File Organization

- [x] Правки — в существующие файлы, новых модулей нет
- [x] Мёртвые корневые дубли скриптов удалены, релиз берёт `scripts/`
- [x] Скрипты и снимки проверки лежат в `scratch/` спеки
<!-- /ANCHOR:file-org -->

---

<!-- ANCHOR:docs -->
## Documentation

- [x] spec.md, plan.md, tasks.md заполнены
- [x] implementation-summary.md заполнен (что сделано, как проверено, ограничения)
- [x] CHANGES.md — запись 68 с пруфами
- [x] Уроки записаны в скилл bazzite-neodon-vpn
<!-- /ANCHOR:docs -->

---

<!-- ANCHOR:fix-completeness -->
## Fix Completeness

- [x] REQ-101..REQ-107 подтверждены приёмкой
- [x] REQ-108: таблица аудита заполнена — 9 исправлено, 5 отложено с причинами
- [ ] Отложенные пункты (A10–A14) вынесены владельцу как следующий шаг
<!-- /ANCHOR:fix-completeness -->

---

<!-- ANCHOR:protocol -->
## Verification Protocol

- [x] Каждая находка аудита проверена самостоятельно до фикса, а не принята по отчёту
- [x] Приёмка шла по пути владельца (тап, свайп, внешняя смена), а не только по коду
- [x] md5 живого файла сверен с репо и с `tests/app`
- [x] Состояние владельца восстановлено (выбор AT, VPN off)
<!-- /ANCHOR:protocol -->

---

<!-- ANCHOR:summary -->
## Verification Summary

| Область | Итог |
|---------|------|
| Прыжки выделения | закрыты (интент выбора, перерисовка на месте, правило второго тапа) |
| Жесты | не выбирают сервер ни в одном проверенном сценарии |
| Флаги | DE на месте, фолбэк — код страны |
| Аудит | 9 фиксов, 5 отложено с причинами |
| Control-plane | `off` больше не врёт |
| Остаток | Decky-панель (нужна сборка бандла) и 4 отложенных пункта |
<!-- /ANCHOR:summary -->
"""

def append(path, chunk):
    with open(path, "a", encoding="utf-8") as f:
        f.write(chunk)
    print("appended", path)

append("spec.md", SPEC_ADD)
append("plan.md", PLAN_ADD)
with open("checklist.md", "w", encoding="utf-8") as f:
    f.write(CHECKLIST)
print("wrote checklist.md")
