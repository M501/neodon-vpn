# Neodon VPN — HANDOFF: полное тестовое покрытие

> **Кому:** инженеру-тестировщику (человеку или нейросети), который напишет полноценный тест-сьют.
> **От:** Hermes (агент-разработчик). **Дата:** 2026-09-26. **Целевой хост:** ROG Ally X, CachyOS (Arch-based), KDE Plasma, Wayland, масштаб 2.1.
> **Правило №0:** это ЛИЧНОЕ устройство владельца (prod). Все тесты по умолчанию — неразрушающие. Тесты, которые останавливают/переключают VPN, допустимы (владелец в курсе), но обязаны в конце возвращать систему в канон: `smart`, профиль `default`, рабочий сервер, состояние CONNECTED.
> **Правило №1:** пароли/ключи доступа в документе отсутствуют намеренно. Доступ к хосту владелец выдаёт отдельно (SSH `m26@<ally-host>`; LAN и Tailscale известны владельцу).

---

## 1. Система одним взглядом

**Neodon VPN** — клиент VPN для портативной консоли: GUI на Python/PySide6 + бэкенд на bash-скриптах + `sing-box` (v1.14.1) как движок. Провайдер — Neodon (подписка v2ray-формата по ссылке; серверы `*.confstage.com/.app`). Аналог v2RayTun по духу: подписка → список серверов → три режима работы → таблица правил маршрутизации (пресеты).

Зачем это всё: владелец в РФ, нужен рабочий доступ к YouTube/Telegram/AI-сервисам **без** потери скорости торрентов/Steam (сплит-туннелинг), с минимумом взаимодействия: одна кнопка включения, всё остальное автоматика.

**Три режима** (фундаментальное требование):

| Режим | Юзер видит | Движок | Маршрутизация | Остановка |
|---|---|---|---|---|
| `smart` | PROXY | `sing-box.service` + `config.json` | tun0; РФ-трафик/торренты/Steam/Ozon напрямую, остальное в VPN; DNS через hijack | без killswitch |
| `full` | TUNNEL | `sing-box-full.service` + `config-full.json` | весь трафик в VPN (fail-closed) + killswitch-allowlist | только через `toggle off` |
| `proxy` | (legacy) | `sing-box-proxy.service` + `config-proxy.json` | socks5 на `127.0.0.1:10808`, без tun | — |

Состояние «выключено» = режим `off` (никаких сервисов, интернет напрямую).

---

## 2. Архитектура и компоненты

### 2.1 GUI
- **Файл:** `~/AI/neodon-vpn/neodon-vpn.py` (~2340 строк, один файл, PySide6).
- **Запуск:** `~/.local/bin/neodon-gui` (`exec /usr/bin/python3 $HOME/AI/neodon-vpn/neodon-vpn.py`), автозапуск через `~/.config/autostart/io.neodon.gui.desktop`; в KDE крутится как transient-юнит `app-Neodon\x20VPN@<hash>.service`.
- **Страницы:** Home (главная), Settings (URL подписки), Logs, Traffic rules (пресеты), Apps, About.
- **Главная (ключевая):** таймер соединения (`#timer`), круглая кнопка питания (`#powerBtn`), пилюля статуса (`StatusPill`), строка сервера (флаг, тег, exit-IP, ping), карточка VPN MODE (кнопки PROXY/TUNNEL), карточка Traffic rules, карточка SERVERS (сетка 2 колонки + Ping + refresh), прогресс квоты подписки.
- **Потоки (QThread):** `CmdWorker` (status-json), `ToggleWorker` (on/off/mode; timeout 25с), `SelectWorker` (смена сервера, фазы), `PingWorker`.
- **Таймеры:** 1с — счётчик времени; 8с — опрос `status-json`; 0.5с — burst-опрос в переходе (окно 12с); 30 мин — автообновление подписки.
- **Трей:** иконка + меню; клик — показать/скрыть окно.
- **Кнопки главной:** `power` (вкл/выкл), `btn_proxy`/`btn_tunnel` (режим; при OFF клик включает VPN в выбранном режиме), сервер-карточки (switch), Ping, refresh подписки, карточка Traffic rules → страница пресетов.

### 2.2 Бэкенд-скрипты (`~/AI/singbox/`)
| Файл | Команды | Назначение |
|---|---|---|
| `singbox-toggle.sh` | `smart\|full\|proxy\|off\|status\|status-json` | Ядро: включение/выключение/режимы. Пишет `.mode`, ставит/снимает `.transitioning`, flock-мьютекс для писателей, dns-fix, killswitch (full), warmup-curl |
| `singbox-server.sh` | `set <N>` (0-based), `list`, без аргументов — интерактив | Смена сервера: конвертер v2ray→sing-box outbound (ws/tls/grpc/reality), `sing-box check`, рестарт активного сервиса, killswitch reinstall (в full), запись `selected-server.json` |
| `killswitch.sh` | `install\|remove` | firewalld-direct allowlist (ACCEPT-правила для сервера и локалок); маркер-лок «filter OUTPUT_direct 20» |
| `dns-fix.sh` | `apply\|restore` | `/etc/resolv.conf` → static `nameserver 1.1.1.1` (hijack-dns внутри tun); restore возвращает stub-symlink. Требует sudo-allowlist (tee/cp/rm/ln) |
| `apply-profile.py` | `<preset-id>` | Пресеты правил: пишет `route.rules` в оба конфига (smart/full), `.profile` |
| `neodon-hostctl` | `status\|start <mode>\|stop\|retry\|server <N>\|profile <id>` | API-мост для GUI/плагина (whitelist-обёртка над toggle/server) |

### 2.3 systemd (user)
- `sing-box.service` (smart), `sing-box-full.service`, `sing-box-proxy.service` — все **disabled by default** (manual power only), `Restart=on-failure`, `RestartSec=3`, `TimeoutStopSec=3`, `ExecStart=/usr/local/bin/sing-box run -c ...`.
- `sing-box` бинарь: `/usr/local/bin/sing-box`, caps `cap_net_admin,cap_net_raw=ep`; legacy-совместимость: симлинк `~/AI/singbox/sing-box`.

### 2.4 Файлы состояния (в `~/AI/singbox/`)
- `.mode` — `smart|full|proxy|off` (намерение).
- `.transitioning` — маркер операции (снимается по завершении; авто-снятие >15с).
- `.toggle.lock` — flock-мьютекс писателей.
- `selected-server.json` — `{tag, server, server_port, updated}`.
- `watchdog-state.json` — `{consecutive_failures, backoff_index, next_due_ts, watchdog_status}` (используется как счётчик здоровья; watchdog-демона на CachyOS нет).
- `transitions.log` (в `~/AI/neodon-vpn/`) — история переходов GUI: `ts OLD->NEW desired=... exit=...`.
- `gui-state.json` — сохранённая геометрия/desired GUI.
- `config.json`, `config-full.json`, `config-proxy.json` — рабочие конфиги sing-box (генерируются из `examples/config*.example` при установке; сервер-часть заменяется `singbox-server.sh`).
- профили: `~/AI/neodon-sub/raw.json` (подписка v2ray), `~/AI/singbox/profiles/*.json` (пресеты правил).

### 2.5 Внешнее
- `firewalld` (direct-правила OUTPUT + killswitch), `polkit` (правило `49-neodon-allow.rules`: `org.freedesktop.resolve1.*` без пароля для wheel), `sudoers` (`/etc/sudoers.d/neodon-vpn` = allowlist: firewall-cmd --direct *, tee/cp/rm/ln resolv.conf, loginctl enable-linger).
- Подписка: HTTPS-ссылка (вводит владелец; двухпроходная загрузка через cookie-jar, т.к. DDoS-Guard).

---

## 3. Контракты взаимодействия (front ↔ back)

### 3.1 `singbox-toggle.sh status-json` — главный контракт
JSON (stdout, одна строка) со полями:
```json
{
  "desired_mode": "smart|full|proxy|off|unknown",
  "profile": "<preset-id>",
  "actual_state": "OFF|STARTING|TRANSITIONING|CONNECTING|CONNECTED|DEGRADED|FAILED|LOCKED|STOPPING",
  "service": "sing-box.service|sing-box-full.service|sing-box-proxy.service|none",
  "service_state": "active|inactive|failed|activating",
  "firewall_rules": 0,
  "tun0": true,
  "exit_ip": "1.2.3.4|null",
  "server_tag": "🇳🇱 [NL] …|null",
  "latency_ms": 42,
  "watchdog_status": "ok|degraded|locked|null",
  "consecutive_failures": 0,
  "next_retry": "…|null"
}
```
Правила вывода состояния: `CONNECTED` ⇔ сервис active ∧ проба выхода успешна (провод: `curl -m 3` + медленный ретрай `-m 6` при фейле и вне перехода; для `full` домашний IP = не-OK); `DEGRADED` ⇔ сервис active, tun есть, но проба не прошла; `FAILED` ⇔ сервис inactive/failed и не locked; `LOCKED` ⇔ правила killswitch остались при мёртвом сервисе (fail-closed); `TRANSITIONING` ⇔ маркер `.transitioning`.
**Бюджет:** ≤1.5с в покое (в т.ч. под нагрузкой торрентов), ≤6с в редком ретрае.

### 3.2 Команды (контракт вызова)
- GUI шлёт бэкенду ровно: `bash ~/AI/singbox/singbox-toggle.sh <mode|off>` (ToggleWorker), `bash ~/AI/singbox/singbox-server.sh set <N>` (SelectWorker), `bash ... status-json` (CmdWorker).
- Возврат toggle: exit 0 + текст («VPN SMART switching...», «VPN OFF — internet via ISP», «FULL FAILED — ...»).
- Коды ошибок не формализованы — кандидат на улучшение (см. §8).

### 3.3 Файлы как контракт
- Желание пользователя — только `.mode` + `gui-state.json.desired`; фактическое — systemctl + `status-json`.
- Тесты, которые трогают `.mode`, обязаны завершать систему командой toggle или ручной записью канона.

---

## 4. Модель состояний (state machine)

Состояния (GUI и бэкенд): `OFF`, `STARTING`, `TRANSITIONING`, `CONNECTING`, `CONNECTED`, `DEGRADED`, `FAILED`, `LOCKED`, `STOPPING`.

Гистерезис GUI (уже реализован, тестировать обязательно): при `CONNECTED` единичные просадки пробы (1–2 подряд) НЕ меняют пилюлю (wobble-guard); 3-я подряд принимается. `OFF/FAILED/LOCKED` принимаются сразу. Смена `desired` (свитч) обходит гистерезис.

Матрица «действие × состояние» — обязательная часть тест-плана (§8.4). Нелегальные переходы (напр. `OFF → CONNECTED` без промежуточного `STARTING/TRANSITIONING`) должны быть недостижимы; тест обязан их проверить на гонках.

---

## 5. Требования (продуктовые)
1. **Manual power only**: НИКАКИХ автоподключений (ни при старте ОС, ни при входе, ни при выборе сервера). Включение — только кнопка питания ИЛИ клик режима/`start` из API по явному действию пользователя.
2. Два VPN одновременно исключены (один tun0, один flock, один `.mode`).
3. `full` — fail-closed: правила killswitch ставятся ДО подтверждения выхода; ошибка = LOCKED, не «тихая дырка».
4. Сплит smart: РФ-сайты/торренты/Steam/Ozon — direct; остальное — VPN; Tailscale (100.64.0.0/10) — всегда direct.
5. UI-бюджеты отзывчивости (замерено, должно сохраняться): toggle off ≤0.6с; toggle on ≤0.8с; свитч сервера smart ≤0.5с; свитч в full ≤5с; status-json ≤1.5с; первый статус после операции ≤0.6с (burst-опрос 0.5с).
6. Никаких всплывающих уведомлений ОС о переключениях (специальное требование владельца; popup-спам выключен, не включать).
7. Размер UI: окно обязано влезать в логический экран 914×514 (scale 2.1); элементы компактные; круглая кнопка питания; без «огромных» отступов.

---

## 6. Что уже покрыто тестами (и чем)

| Инструмент | Что покрывает | Где |
|---|---|---|
| `~/AI/singbox/qa-gui-states.sh` | 8 e2e-кейсов тап-инжектом (power off/on, быстрый ре-тап, PROXY↔TUNNEL, включение из OFF кликом режима, стабильность пробы под нагрузкой) | хост + repo `scripts/` |
| `scripts/qa-touch.py` | uinput-тап (программный палец; `sudo chmod 666 /dev/uinput` разово) | хост |
| `release/qa-static.sh` | комплектность tarball, синтаксис, секрет-скан | любая машина |
| `release/qa-sandbox.sh` | установка в фейковый HOME, «живое не тронуто» | хост |
| `install.sh --dry-run` | прогон инсталлятора без изменений | хост |
| Скилл `neodon-e2e-qa` | методика (сервер-матрица, пресет-матрица, питфоллы) | Hermes |

**Честная оценка: это НЕ полное покрытие.** Покрыт базовый happy-path GUI и статический QA релиза. Не покрыто: все страницы GUI, пресеты правил (11 шт.), отказы (мёртвый сервер, обрыв сети, permissions), подписка, установщик на чистой системе, гонки, soak, sleep/resume, leak-тесты, локализация, производительность под нагрузкой в full и т.д. Ниже — ТЗ на полное покрытие.

---

## 7. ТРЕБОВАНИЕ: полное тестовое покрытие (ТЗ)

**Цель:** автоматизированный сьют, который можно гонять на живом хосте (и в CI-песочнице) после каждого изменения, с машиночитаемым отчётом. Разрешается использовать: bash, python3 (stdlib; при нужде — pytest + pytest-qt в venv), текущие инструменты из §6, `systemd-run --user` для замеров. Запрещено: выдумывать сущности, не описанные здесь; ломать живой прод без восстановления; светить секреты.

### 7.1 Уровни
- **L1 Unit** (быстро, offscreen): парсеры (конвертер v2ray→sing-box: ws/tls/grpc/reality/flow; JSON убийственно валидируется), форматтеры (пилюля/статусы), логика on_power (intent/queue), `_fast_poll_wanted`, парсинг `status-json`.
- **L2 Component**: каждый скрипт бэкенда в изоляции (toggle/server/killswitch/dns-fix с фейковым HOME/SRC), коды возврата, идемпотентность.
- **L3 E2E-функциональные**: живой хост, реальные сервисы, тап-инжект GUI.
- **L4 Release/Install**: тarball, установка на чистую (sandbox+VM/оффлайн), апгрейд поверх.

### 7.2 Полная матрица тест-кейсов (минимальный состав; расширять приветствуется)

**A. Кнопка питания (все состояния):** tap при OFF/STARTING/TRANSITIONING/CONNECTED/DEGRADED/FAILED/LOCKED/STOPPING → ожидаемый переход + отсутствие «съеденных» кликов (занято → очередь last-wins, не игнор). Двойной/тройной тап с интервалами 0.3/1/2/5с. Тап во время burst-обновления.

**B. Режимы:** PROXY↔TUNNEL при ON (оба направления), из OFF (включает), повторный клик активного режима (no-op, кнопка не «мертвая»), переключение во время TRANSITIONING (очередь).

**C. Серверы:** все N серверов из подписки: `set` в smart и в full (включая проверку killswitch reinstall и смены маршрута в логах), клик сервера в GUI, сервер с каждым типом транспорта (ws/tls, ws/none, grpc/tls, grpc/reality, tcp/reality + flow), мёртвый сервер (ожидание: DEGRADED/пометка, не зависание), смена сервера во время активной закачки (торрент).

**D. Состояния/пилюля:** все надписи (Connected/Connecting…/Switching…/Stopping…/Reconnecting…/Failed/Protected — VPN unavailable/Not connected) в соответствующих состояниях; wobble-guard: 1-2 быстрые просадки пробы не меняют пилюлю, 3-я меняет; «exit IP» отображается и меняется при свитче; таймер соединения не сбрасывается при ложных DEGRADED (только при реальных OFF/reconnect).

**E. Подписка:** refresh из GUI (иконка), refresh после протухшей ссылки, отсутствие ссылки (ошибка в статусбаре, не краш), квота (bytes→GiB), автообновление (30 мин), двухпроходная загрузка (DDG cookie-jar).

**F. Пресеты правил (11):** каждый пресет: apply → валидность конфига (`sing-box check`), изменение `.profile`, проверка первых правил по логам маршрута (karl: direct vs proxy), возврат в `default`. Минимум — smoke на каждый + e2e на 3 базовых.

**G. Killswitch/DNS/leak (full):** правила ставятся до подтверждения выхода; после свича сервера allowlist обновлён (IP нового сервера); `toggle off` снимает правила; утечка при мёртвом сервисе — отсутствует (fail-closed); DNS: resolv.conf static ↔ stub; при `off` — восстановлен.

**H. Отказы и восстановление:** убить sing-box (kill -9) → Restart=on-failure поднимет; оборвать сеть (rfkill/ip link) → DEGRADED→CONNECTED при возврате; мёртвый сервер при включении; диск полный (логи); permission denied (отзыв sudoers) → деградация без краха; рестарт GUI во время перехода; OOM/высокая нагрузка (торрент+YouTube+переключения).

**I. Install/upgrade:** `--dry-run` exit 0 без мутаций; sandbox-установка (фейковый HOME); установка поверх живой (идемпотентность: повторный запуск не ломает, не дублирует); «Install Neodon VPN.desktop» с рабочего стола; uninstall (--uninstall) не удаляет секреты.

**J. Производительность (бюджеты §5):** тайминги всех операций из §5 под нагрузкой (торрент ≥1.8 MiB/s) и без; заметить деградации >20%; отдельный тест «ложный DEGRADED»: под нагрузкой 30× status-json — доля непустых exit_ip ≥ 90%.

**K. UI/UX:** адаптив окна (вписывается в 914×514; min-size); круглая кнопка (регресс «квадратная»); компактность (в кадре без скролла: таймер/кнопка/пилюля/сервер/режимы/правила); отсутствие popup-спама (уведомления ОС за 5 минут операций: 0 шт.); сайдбар-навигация (home/settings/logs/traffic/apps/about) — каждая страница открывается, не крашится; единичный инстанс (второй запуск не дублирует окно).

**L. Регрессия (гейт):** `qa-gui-states.sh` 8/8 после каждого изменения бэкенда/GUI; все L1-L2 зелёные; отсутствие новых записей в журналах `Traceback`/`syntax error`.

### 7.3 Формат сдачи
- Сьют в репо: `tests/` — L1/L2 (pytest, `QT_QPA_PLATFORM=offscreen`), `qa/` — bash-раннеры L3/L4 (по образцу `qa-gui-states.sh`), единый `qa/run-all.sh` с итогом PASS/FAIL и exit-кодом = числу FAIL.
- Каждый кейс: id (A1..L9), предусловие, шаги, оракул (что именно проверяем в JSON/логе/пикселях), cleanup (возврат в канон).
- Отчёт: markdown + машинный JSON (`{case, status, ms, details}`).
- Всё, что использует sudo/uinput/firewalld — с явной пометкой и graceful-skip, если нет прав.

---

## 8. Инструментальные заметки (проверенные кровью)
- **SSH-команды только через файлы-скрипты**: шелл хоста — fish, inline-конструкции с `$()`/`=` падают. Пиши `*.sh` → `scp` → `bash file.sh`.
- **Скриншоты:** `spectacle -b -n -o file.png` ТОЛЬКО с env `XDG_RUNTIME_DIR=/run/user/1000 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus WAYLAND_DISPLAY=wayland-0`; иначе xcb-crash.
- **Тапы:** `python3 qa-touch.py tap X Y` (координаты — физические 1920×1080). Разово: `sudo chmod 666 /dev/uinput`. Координаты кнопок ищутся пиксельно (PIL: заливка `#2A5FD8`, круг ⌀~134 px) или vision-оценкой (±30 px достаточно).
- **GUI-потоки:** операции — не в главном потоке (QThread); «залипший TRANSITIONING» лечится маркером-таймаутом (15с) и `_drain_pending`.
- **Поллинг статуса:** 8с в покое, 0.5с burst в переходе (12с окно). Не увеличивать интервал покоя — UX-бюджет.
- **Торрент-нагрузка меняет тайминги проб** (см. §J) — все пороги проверять и под нагрузкой.
- **Синтаксис-гейт:** любой `.sh` прогонять `bash -n`; любой `.py` — `py_compile` ДО деплоя (был инцидент: комментарий съел `fi` → прод-скрипт молча падал).

## 9. Приложение A — канон и полезные команды
```bash
# канон после любых тестов
bash ~/AI/singbox/apply-profile.py default
bash ~/AI/singbox/singbox-toggle.sh smart
bash ~/AI/singbox/singbox-server.sh set <рабочий N>   # рабочие: 0,1,2,3,5,7,8,9,10; [4],[6] мертвы у провайдера
# статус
bash ~/AI/singbox/singbox-toggle.sh status-json
# тап-тест
bash ~/AI/singbox/qa-gui-states.sh
```
## 10. Приложение B — известные дефекты внешней среды (не баги продукта)
- Серверы `[4] DE` и `[6] RU` не отвечают (сторона провайдера) — тестам использовать рабочие индексы.
- Мёртвые торрент-пиры в логах (`dial tcp … i/o timeout` от qbittorrent) — шум, не ошибка VPN.
- KDE-масштаб 2.1 (логический экран 914×514) — учитывать при UI-тестах.

**Критерий готовности этого ТЗ:** сьют гоняется одной командой на живом хосте ≤15 минут, покрывает ≥95% кейсов выше, возвращает систему в канон, и его отчёт позволяет отличить «продукт сломан» от «среда/сервер шумит».
