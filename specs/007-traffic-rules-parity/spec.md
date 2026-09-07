# Spec 007 — traffic rules: паритет доказан, UI честный (flow-track)

## Вопрос владельца
«Что в трафик-правилах происходит»: галочки, что куда идёт, бутафория ли.

## Как устроено (факт)
Таб = 11 пресетов v2RayTun (структура 1:1: globalProxy/bypassLan/direct/
proxy/block). «Галочка» = radio активного + бейдж verified (4/11).
Активный пресет = генерированный sing-box конфиг (15 route.rules inline).

## Паритет с v2RayTun (доказано)
- Формат: эталон `.RU без VPN` = direct[avito.st, category-ru, regexp ru],
  proxy[], global ON — наш порт 1:1 (verified True у обоих).
- yandex: в эталоне только через category-ru → direct; у нас так же
  (suffix + keyword). Рутрекер-канарейка: обе стороны через proxy.
- Оракул `probe_routing.py` (детерминированный матчинг): 23/23 домена
  совпали с замыслом ru-bez-vpn (RU→direct, остальное→final proxy).
- Live с атрибуцией журнала: rutracker→proxy 301, youtube→proxy 301,
  ya.ru→direct (302; один transient dial-timeout 5с при ротации egress —
  повтор 326мс; класс wobble, покрыт гистерезисом пилюли).
- TUNNEL-пресеты игнорит по дизайну (fail-closed full) — так и написано.

## UI (было «заглушка»)
- На каждой карточке census: «напрямую: N зап. · через VPN: M зап. ·
  категории: …» / «без доп. записей». Только counts, без заявлений.
- Бейджи не трогал: переворачивать в True без live-матрицы = бутафория.
  Матрицы остальных 10 пресетов — recurring job по regression-policy.

## Verify
25/25 pytest (summary+render-тесты, рендер проверен vision) → деплой →
рестарт → CHANGES + push.
