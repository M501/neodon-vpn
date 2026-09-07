# Spec 002 — тапы-мимо и ощущаемая медлительность свитчей (flow-track)

## Проблема (живой палец владельца)
1. Отпуск пальца после скролла открывает Traffic rules: `_ClickFrame.mouseReleaseEvent` стреляет на ЛЮБОЙ release внутри rect, не отличая тап от конца драга.
2. Свитч proxy/tunnel и on/off ощущаются ~10с при реальном бэкенде 0.5–4с: `flock 9` в шапке toggle держит ВСЕ вызовы, включая read-only `status-json` (curl+pythons, p99 секунды) → toggle ждёт за опросами. Плюс toggle() не ставит TRANSITIONING сразу — ноль фидбэка до конца воркера.

## Scope
- GUI: `_ClickFrame` tap-vs-drag (slop 12px), `toggle()` optimistic (`set_state TRANSITIONING` первой строкой).
- `singbox-toggle.sh`: flock только для мутаций; `status|status-json` — `flock -n ... || true` (fail-open, read-only безопасен: marker/mode/profile читаются атомарно).
- Тесты: QTest press/move/release по фрейму; optimistic pill; live-замер `status-json` под занятым локом <2с.

## OUT
Редизайн, интервалы опроса (уже 8с), fast-path status (отдельно), дефолт сервера.

## Verify
pytest на хосте зелёные → py_compile + `bash -n` → деплой → live: status под локом мгновенный, toggle smart→proxy→smart с таймингами из transition-журнала → CHANGES + push + DONE/CAVEATS.
