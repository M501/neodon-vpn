# Spec 028 — English UI + uptime + traffic-rules footnote (flow-track)

## Запрос владельца
- Счётчик аптайма в QAM между VPN и тумблером, в одну строку, как в десктопе.
- «Профиль» — не профиль, а Traffic rules; имя — настоящее десктопное,
  отдельной строкой внизу со сноской «from the desktop app».
- ВЕСЬ интерфейс на английском (десктоп + гейм-мод), Bazzite на английском.

## Решение
- QAM: `VPN · H:MM:SS` в label тумблера (клиентский счётчик, сброс при
  реконнекте — как десктопный таймер). `Traffic rules: <name>` + сноска
  `* rules come from the desktop app`. Весь текст панели EN.
- Бэкенд: PRESET_NAMES (id→EN, зеркало PRESETS) + `profile_name` в get_status.
- Десктоп: ~45 UI-строк RU→EN (пресеты, кнопки, хинты, статусы, трей,
  подписка, канарейки). Комменты/данные провайдера не тронуты.
- Тесты дрейфа: `preset-names-cover-desktop` (карта ⊇ PRESETS из прод-файла).

## Пруфы
- 52/52 pytest на хосте + 9/9 backend (profile-name, cover-desktop).
- Harness зелёный. DIST свежий, backend up, журнал чист.
