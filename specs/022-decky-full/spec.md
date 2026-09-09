# Spec 022 — Decky-плагин полного паритета (paper-track)

## Требование владельца
В Game Mode ВЕСЬ функционал десктопа: proxy/tunnel вкл, смена сервера,
статус. Не урезанная обёртка, а полный паритет управления.

## Архитектура (консилиум + R2)
- Тонкий Decky QAM-плагин (React TS + Python backend, root-флаг) поверх
  существующего bash-контракта: `toggle.sh up/down/status-json`,
  `server.sh list/set`, `.mode`/профиль read-only. Ноль дублирующей логики.
- QAM-панель (геймпад, крупный шрифт): статус-точка + exit IP, сегмент
  PROXY/TUNNEL/OFF, список серверов (имя+пинг, без текстового ввода),
  Переподключить, квота (read-only из sub-cache).
- Конфиг/подписки/пресеты — только Desktop. Game Mode только управляет.
- Fallback: non-Steam шорткат Qt без доработок.

## Безопасность (red lines скептика)
- Root только через wrapper allowlist (`up|down|status`), regex-валидация,
  никакого shell=True/f-строк, никакого парсинга конфигов в root.
- Подписи релизов до запуска; uninstall; без silent-update.

## Шаги
1. `ujust setup-decky` + TunnelDeck из стора на железе (валидация пути).
2. Каркас плагина (plugin.json root + main.py-обёртки + QAM-панель).
3. Прогон матрицы из Game Mode (те же инварианты, что в Desktop).
