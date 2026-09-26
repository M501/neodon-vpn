# Neodon VPN QA Suite

Тестовый сьют по HANDOFF от 2026-09-26. Он разделён на два класса:

- **L1/L2** — безопасные проверки контракта, синтаксиса, структуры конфигов/профилей и `install.sh --dry-run`.
- **L3/L4** — live/E2E и install/upgrade проверки. Они не стартуют разрушительные действия по умолчанию.

## Безопасность

Прод-хост считается чувствительным. По умолчанию live-тесты только диагностические. Для операций, которые переключают VPN, убивают сервис, меняют firewall/DNS или инжектят touch, нужны явные переменные:

```bash
export NEODON_LIVE=1
export NEODON_ALLOW_DISRUPTIVE=1
export NEODON_ALLOW_FIREWALL=1        # только для full/killswitch тестов
export NEODON_ALLOW_UI_INPUT=1        # только для uinput tap-тестов
export NEODON_WORKING_SERVER=0        # при необходимости переопределить
```

Все live-скрипты ставят `trap` и при завершении пытаются вернуть канон:

```text
profile=default
mode=smart
server=$NEODON_WORKING_SERVER
actual_state=CONNECTED
```

Если канон вернуть не удалось, runner завершится с FAIL и отдельно пометит проблему cleanup.

## Предполагаемая раскладка

Сьют ожидает запуск из корня проекта Neodon или через `NEODON_REPO`:

```bash
export NEODON_REPO="$HOME/AI/neodon-vpn"
```

При стандартной установке backend ожидается в `~/AI/singbox`.

## Быстрый запуск

Из корня проекта:

```bash
bash qa/run-all.sh
```

Только безопасный L1/L2:

```bash
bash qa/run-all.sh --static
```

Live/E2E:

```bash
NEODON_LIVE=1 bash qa/run-all.sh --live
```

Отчёты:

```text
qa-results/report.json
qa-results/report.md
```

Коды: `0` = нет FAIL, `N` = число FAIL. `SKIP` и `WARN` не превращаются в FAIL.

## Что реализовано

### L1

- контракт `status-json` и допустимые enum/типы;
- `selected-server.json`;
- наличие и синтаксис известных shell/python entrypoint'ов;
- Python compile gate;
- безопасный secret-scan по текстовым файлам;
- базовая проверка state-machine инвариантов как статических контрактов.

### L2

- `sing-box check` для доступных рабочих конфигов;
- smoke для 11 профилей, если каталог профилей присутствует;
- `install.sh --dry-run`, если installer присутствует;
- идемпотентный статический smoke структуры backend.

### L3/L4

Live-сценарии реализованы как отдельные bash-раннеры и graceful-skip'аются, когда нет live-флага/прав/инструментов:

- A/B: power/mode state machine;
- C: серверная матрица;
- D: статус/exit IP/wobble-проверки на уровне backend telemetry;
- E: subscription smoke без раскрытия URL;
- F: profile e2e smoke;
- G: full/killswitch/DNS, только при явном allow;
- H: controlled service-kill recovery;
- I: release/install checks;
- J: timing/soak;
- K: screenshot/UI sanity, только при явном uinput и Wayland env;
- L: обязательный регрессионный gate `qa-gui-states.sh`.

## Ограничение

Репозиторий приложения в исходных материалах не был приложен, поэтому неизвестные внутренние функции GUI (например, точные Python-имена `_fast_poll_wanted`, `on_power`, конкретные Qt-объекты) намеренно не выдумываются. Для них оставлены contract/live gates, а не фиктивные unit-тесты.
