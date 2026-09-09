# Regression policy — что гонять и когда (RCRCRC + пирамида)

## Пирамида (Google: тонкий E2E-слой)
1. `pytest test_gui_logic.py` на хосте (0.5с) — ВСЕГДА, после любого изменения GUI.
2. Backend-матрица (toggle/mode/server ×N + тайминги + leak A/B) — при изменениях
   `singbox-toggle.sh`, `killswitch.sh`, `singbox-server.sh`, пресетов.
3. Живой GUI (скрин + vision + transitions.log) — при изменениях подсветки,
   пилюли, тапов, уведомлений.
4. Motion (GSR 3–15с + PTS gaps) — только при жалобах на анимации/лаги/тач.

## Отбор регрессии (RCRCRC)
Recent (чинилось на этой неделе) + Core (питание/режимы/сервер/подписка) +
Risky (файрвол, DNS) + Config (пресеты, сервер idx0 vs idx2) + Repaired (баг
из transitions.log владельца) + Chronic (флипы, мигания таймера).

## Правило плохого прогона
Живой прогон без status-json + transitions.log + (для движения) видео =
не доказательство. Каждый FAIL сначала: «баг теста или продукта?»
(классика: IP цели vs выходной, `1.1.1.1 в allowlist по дизайну`,
CRLF после Windows-правок `.sh`, IPv6-дубли в логах).

## Канон после прогонов
Режим/профиль/сервер вернуть как было (сейчас: smart / ru-bez-vpn / idx2),
GUI перезапущен одним инстансом, GSR убит (`ps`), transitions.log не забит.
