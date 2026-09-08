# Spec 014 — пресет для россиянина (flow-track)

## Вопрос
Какой пресет самый покрывающий для RU (Ozon/торренты/Steam/vk напрямую,
блокировки в VPN), оставлять ли один.

## Ответ (живой тест)
- `russia-mimo` применён, config-пробы: ya/vk/ozon direct, youtube/rutracker
  proxy. Но: близнец ru-bez-vpn (delta = private, покрыт base ip_cidr).
- Вердикт: оставаться на ru-bez-vpn (больше live-пруфов), mimo — запасной,
  verified обоим + popular-ai. Остальные 6 — выбор, не мусор (0 cost).
- The Finals voice покрыт базовым UDP-3478→proxy на любом пресете.
