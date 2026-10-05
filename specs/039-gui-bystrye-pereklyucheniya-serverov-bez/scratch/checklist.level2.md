---
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

## Verification Protocol

- [x] CHK-101 [P0] Каждая находка аудита проверена самостоятельно до фикса, а не принята по отчёту
- [x] CHK-102 [P0] Приёмка шла по пути владельца (тап, свайп, внешняя смена), а не только по коду
- [x] CHK-103 [P0] md5 живого файла сверен с репо и с `tests/app`
- [x] CHK-104 [P0] Состояние владельца восстановлено (выбор AT, VPN off)
<!-- /ANCHOR:protocol -->

---

<!-- ANCHOR:summary -->

## Pre-Implementation

- [x] CHK-105 [P0] Жалоба владельца зафиксирована в spec.md
- [x] CHK-106 [P0] Корневые причины измерены на устройстве (лог карточек, спай событий, гэпы, пиксельная проверка флагов)
- [x] CHK-107 [P0] Бэкапы живой копии созданы до деплоя (`.pre039`)
- [x] CHK-108 [P0] Точки отката описаны (GUI, репо, control-plane, ассет)
<!-- /ANCHOR:pre-impl -->

---

<!-- ANCHOR:security -->

## Code Quality

- [x] CHK-109 [P0] `python -m py_compile` на обеих копиях GUI — PASS
- [x] CHK-110 [P0] `bash -n` для правленого скрипта — PASS
- [x] CHK-111 [P0] Мёртвый код удалён, а не закомментирован
- [x] CHK-112 [P0] Комментарии объясняют WHY (замеры), без эфемерных меток спек
<!-- /ANCHOR:code-quality -->

---

<!-- ANCHOR:testing -->

## Testing

- [x] CHK-113 [P0] Одиночный тап выбирает сервер (контроль)
- [x] CHK-114 [P0] Двойной тап 150 мс: второй тап доходит, подсветка без прыжков
- [x] CHK-115 [P0] Двойной тап 250 мс: то же
- [x] CHK-116 [P0] Протяжка вниз при неподвижном скролле: выбора нет
- [x] CHK-117 [P0] Вертикальный свайп: прокрутка есть, выбора нет
- [x] CHK-118 [P0] Горизонтальные свайпы в обе стороны: сдвиг 0, выбора нет
- [x] CHK-119 [P0] Внешний `set N` (как из панели): подсветка переезжает
- [x] CHK-120 [P0] Флаг DE подтверждён пикселями карточки
- [x] CHK-121 [P0] Все страницы GUI открываются после удаления мёртвого UI
- [x] CHK-122 [P0] Честный `off`: 0 правил prio 20, интернет через провайдера, юниты inactive
<!-- /ANCHOR:testing -->

---

<!-- ANCHOR:file-org -->

## Fix Completeness

- [x] CHK-123 [P0] REQ-101..REQ-107 подтверждены приёмкой
- [x] CHK-124 [P0] REQ-108: таблица аудита заполнена — 9 исправлено, 5 отложено с причинами
- [ ] CHK-125 [P0] Отложенные пункты (A10–A14) вынесены владельцу как следующий шаг
<!-- /ANCHOR:fix-completeness -->

---

<!-- ANCHOR:protocol -->

## Security

- [x] CHK-126 [P0] Ссылка подписки не может закрыть строку в конвертере (отказ на кавычки, бэкслеши, переводы строк)
- [x] CHK-127 [P0] Временные файлы refresh больше не фиксированные во `/tmp` (имена с PID)
- [x] CHK-128 [P0] Дочерние процессы не получили новых прав, `sudo` остаётся только `-n`
- [x] CHK-129 [P0] Секреты и токены не попадали в вывод и в файлы отчётов
<!-- /ANCHOR:security -->

---

<!-- ANCHOR:code-quality -->

## Documentation

- [x] CHK-130 [P0] spec.md, plan.md, tasks.md заполнены
- [x] CHK-131 [P0] implementation-summary.md заполнен (что сделано, как проверено, ограничения)
- [x] CHK-132 [P0] CHANGES.md — запись 68 с пруфами
- [x] CHK-133 [P0] Уроки записаны в скилл bazzite-neodon-vpn
<!-- /ANCHOR:docs -->

---

<!-- ANCHOR:fix-completeness -->

## File Organization

- [x] CHK-134 [P0] Правки — в существующие файлы, новых модулей нет
- [x] CHK-135 [P0] Мёртвые корневые дубли скриптов удалены, релиз берёт `scripts/`
- [x] CHK-136 [P0] Скрипты и снимки проверки лежат в `scratch/` спеки
<!-- /ANCHOR:file-org -->

---

<!-- ANCHOR:docs -->

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
