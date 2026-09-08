# Spec 013 — мусор вывезен: V1-пара удалена везде (flow-track, irreversible)

## Команда владельца
Удалить неиспользуемые старые пресеты; + вопрос: правда ли работал один.

## Ответ на вопрос
Да: активен всегда ровно один пресет (radio и у нас, и в v2RayTun —
`settings_pref_routing_preset_enabled` + выбранный). Остальные — спящие
варианты, не параллельные движки. Галочка у одного = норма обеих систем.

## Удалено (V1: ai, anti-censorship)
- GUI: PRESETS (11→9), CANARIES, комментарий.
- Host: profiles/{ai,anti-censorship}.json, apply-profile PROFILES/usage/
  fallback, hostctl whitelist. apply-profile.py принят в репо (truth).
- Мусор: 3× profiles.bak-full-* + 12 patcher-`.bak-*` с хоста.
- Оставлено: config*.bak (rollback server.sh — runtime!), 8 портов v2RayTun
  (selectable options, matrix-coherent; снос = снос фичи) + default fallback.

## Verify
- `profile ai` → reject rc=2; popular-ai→ru-bez-vpn applied; CONNECTED.
- 35/35 pytest; audit legacy→default; деплой GUI + рестарт → CHANGES + push.
