# Boundaries — границы и классы (EP + BVA по реальному UI Neodon VPN)

Правило: 1 значение на класс (EP), границы ± сосед (BVA 2-value).
3-value только там, где помечено [3V] (killswitch, деньги подписки).

## Режимы × питание (decision table — полный перебор, 3×4)
| state \ click | power | PROXY | TUNNEL | server |
|---|---|---|---|---|
| OFF | →mode | →smart+on | →full+on | select only |
| CONNECTED | →off | noop/same | →full | set+keep |
| TRANSITIONING | settle-ignore | busy-ignore | busy-ignore | busy-ignore |
| LOCKED/FAILED | →off(unlock) | →smart | →full | set+keep |

## Числовые границы
- Индекс сервера: 0 / N-1 ок; -1 / N → «Неверный сервер» (тест!).
- Подписка: total=0 → N/A + причина (не молча); used/total 99% → отображение.
- Таймауты проб: exit -m steady 2 / transition 5; latency TCP 1с; CmdWorker 10с.
- Опросы: steady 8с; burst 1.5с 12с после toggle; settle питания 5с.
- Счётчики: streak 3 (пилюля+эпоха); transitions.log кап 20Кб/150 строк.
- Файрвол: LOCKED = наличие REJECT (не счётчик!); allows persist by design.

## Count 0/1/Many
- Серверов 0 (подписка пуста) / 1 / N; пресетов: активный 1, остальные 10.
- Правил: 0 (default) / 16 allows / 40+ с endpoint-IP.

## Состояния соединения (state transition, включая недопустимые)
OFF→TRANSITIONING→CONNECTED→{DEGRADED→CONNECTED | OFF}; OFF→LOCKED→OFF;
запрещены: CONNECTED→OFF без OFF-визита в transitions.log; OFF→CONNECTED
без TRANSITIONING (кроме старта GUI).
