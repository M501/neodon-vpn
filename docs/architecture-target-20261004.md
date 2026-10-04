# Neodon — целевая архитектура VPN-управления (v2)

**Статус:** Target Architecture — согласована в раунд-таблице Hermes ↔ ChatGPT web (3 раунда, 04.10.2026)
**Платформа:** ROG Xbox Ally X (Ryzen Z2 Extreme) / CachyOS / Steam Game Mode first, Desktop Mode вторично
**Ядро:** sing-box 1.14 (технические факты сверены с официальной документацией и исходниками v1.14)
**Скоуп:** SMART/FULL VPN, failover серверов, DNS, жизненный цикл подписки, UX панели QAM и десктоп-GUI

---

## 0. Почему v2 — диагноз текущей системы

Сегодняшний стек — «UI + shell + systemd timers + watchdog одновременно пытаются быть диспетчером»:
- смена сервера = патч 3 JSON-конфигов + `sing-box check` + рестарт юнита + файлы-маркеры (`.transitioning`, TTL), эхо-гварды UI;
- состояние размазано по файлам `.mode` + `.desired` + маркерам, которые могут расходиться;
- watchdog смешивает три разных события: «VPN-сервер мёртв», «сеть мертва», «DNS мертв»;
- DNS-резолв через мёртвый прокси роняет весь интернет (главный инцидент);
- UI ждёт 5-секундные поллы и показывает внутреннюю механику (`TRANSITIONING`, `FAILED`) вместо результата.

Главная проблема — **смешение ownership**, а не количество компонентов. Следствие — хрупкость и медленное добавление фич.

## 1. Цели (требования владельца)

1. Game Mode first: управление из QAM за 1–2 действия; Desktop GUI согласован.
2. **Интернет не умирает**: при отказе сервера в SMART — быстрый прозрачный failover; если живых нет — direct fallback с честным сообщением. FULL — fail-closed, но с ограниченным recovery-window и явным авто-выключением.
3. Смена сервера: мгновенный отклик, результат за секунды, без рестарта ядра; мёртвый сервер виден сразу.
4. Магазин Decky и заблокированные сервисы работают при живом VPN.
5. Человеческий язык в UI; никакой внутренней механики на экране.
6. Сон / потеря Wi-Fi / возврат — восстановление без вмешательства.
7. Простота: один владелец политики, прозрачные логи.

## 2. Архитектурные принципы

- **Один writer на state domain** (не «один файл истины на всё»):

| Domain | Authority |
|---|---|
| User intent (enabled/mode/preferred_server) | singbox-manager (persistent state) |
| Current selected outbound | running sing-box |
| Health/выбор кандидата | sing-box URLTest |
| Process lifecycle | systemd (только супервизор) |
| Kernel/network/firewall reality | OS / privileged helper |
| UI | read-only клиент (никогда не истина) |

- **User intent ≠ runtime state**: `preferred_server` («хочу DE-3») и `active_server` («сейчас PL-2 из-за failover») — разные сущности; автовозврат к preferred запрещён (анти-флаппинг).
- sing-box = dataplane (TUN, routing, DNS, nodes, selector, urltest, Clash API). Manager не дублирует.
- Manager = policy + lifecycle + recovery + subscription; маленький, «решает какой policy применить».
- UI = тупой клиент единого status-документа.

## 3. Компоненты

```
 Decky QAM  ──┐
              ├──► localhost Manager API ──► singbox-manager ──► Clash API 127.0.0.1 ──► sing-box
 Desktop GUI ─┘                                (policy/intent/       (selector/urltest/    (TUN/routing/DNS)
                                               lifecycle/recovery)    connections)
                                                      │
                                                      └──► privileged helper (firewall / resolv / tun cleanup)
```

## 4. sing-box топология

- 12 outbound'ов нод с **стабильными тегами** (`proxy-de-1`, `proxy-pl-2`, …), у нод `connect_timeout: 3s`.
- **URLTest** `auto` (baseline; после замера квоты можно 120s):
  ```json
  { "type": "urltest", "tag": "auto", "outbounds": ["proxy-…", "…"],
    "url": "https://api.ipify.org", "interval": "60s", "tolerance": 100,
    "idle_timeout": "24h", "interrupt_exist_connections": false }
  ```
  Механика v1.14: проба = HTTP HEAD, общий таймаут пробы 15s; при фейле history ноды удаляется → нода вне выбора; следующая попытка на новом свипе. «Полуживые» (TCP ок, TLS умирает ~20s) отсекаются по таймауту.
- **Один внешний Selector** `active`:
  ```json
  { "type": "selector", "tag": "active",
    "outbounds": ["proxy-… ×12", "auto", "direct"],
    "default": "auto", "interrupt_exist_connections": false }
  ```
  Управляется ТОЛЬКО через Clash API (`PUT /proxies/active`). `direct` — член селектора только для SMART-политики.
- `cache_file.enabled=true` → выбранный selector переживает рестарт ядра (store_selected включён по умолчанию); cache — только runtime persistence, НЕ замена manager-состоянию.

## 5. Routing semantics

- `route.final = active`; proxy-правила указывают `active`; direct-правила — `direct`.
- Следствие: `active=DE-3` → proxied-трафик через DE-3; `active=auto` → через выбранную urltest-ноду; `active=direct` → proxied-трафик деградирует в direct (это и есть SMART fallback).

## 6. DNS архитектура (убираем deadlock)

Классификация доменов у DNS — **та же**, что у трафика (один список, не две копии).

- `dns-direct`: `udp 1.1.1.1:53`, `detour: direct` — default;
- `dns-proxy`: `tls 1.1.1.1:853` (DoT, `server_name: cloudflare-dns.com`), `detour: active` — для proxy-доменов;
- dns.rules: `proxy-domains → dns-proxy`; всё остальное → `dns-direct`; `final: dns-direct`.

Семантика отказа: `active=DE-3` → DNS proxy-доменов идёт через DE-3; DE-3 умер → `active=auto` → через живой; тотал в SMART → `active=direct` → DNS вообще не падает (direct). **DNS больше не единая точка отказа.**

- В 1.14 `dns.rules[].outbound` — deprecated; использовать современный синтаксис (`action: route` + `server`); проверить `sing-box check` при внедрении.
- sniff для DNS-пути не нужен (имя уже в запросе).
- systemd-resolved — переходный дизайн (Phase 1 допустимо): VPN ON → `resolv.conf → 127.0.0.1:53` (sing-box; способ листенера проверить на 1.14), VPN OFF → `127.0.0.53` (resolved). Полный takeover через встроенный resolved-сервис sing-box — Phase 5, не MVP.

## 7. State model (три ортогональных домена)

- **Intent**: `enabled: bool`, `mode: smart|full`, `preferred_server: id`.
- **Network**: `UNKNOWN | ONLINE | NETWORK_DOWN | RECOVERING`. NETWORK_DOWN ≠ VPN dead: recovery-решения замораживаются, эскалации в UI паузятся; после возврата сети — reconcile + форс health-проверки.
- **VPN runtime**: `OFF → STARTING → SMART_ACTIVE | SMART_DEGRADED_DIRECT | FULL_ACTIVE | FULL_RECOVERING → FULL_EMERGENCY_OFF(=OFF)`.
  - SMART_DEGRADED_DIRECT: intent on, `active=direct`, интернет жив, «VPN requested but unavailable», ретраи в фоне.
  - FULL_EMERGENCY_OFF: recovery исчерпан (N минут) → VPN off + killswitch снят + direct-интернет + явное пользовательское событие; intent.enabled честно переводится в false.

## 8. Failover / флаппинг / соединения

- Current-path probe (только effective сервер): 2 подряд неудачи + network ONLINE → сервер считается мёртвым → `active=AUTO` → валидация выбранной ноды → событие в UI. Нет живых → `SMART_DEGRADED_DIRECT`. Частота baseline 10s (обсудить 5s).
- URLTest отвечает за health/выбор кандидата; **не** отвечает за «весь VPN умер» (при полном отсутствии history у него есть first-outbound fallback) — это решает manager.
- Анти-флаппинг: tolerance 100ms; preferred не возвращается автоматически; одиночный hiccup не триггерит failover.
- Соединения: manual switch — старые TCP не трогаем; failover — точечно `GET /connections` → фильтр по chain старого сервера → `DELETE /connections/{id}` (НЕ глобальный DELETE). `interrupt_exist_connections` не считать основным механизмом (в 1.14 известна проблема с routed connections).

## 9. Subscription lifecycle

`download → parse → generate config → sing-box check → atomic replace → restart sing-box (единственный допустимый рестарт) → reconcile policy`.
- В 1.14 **PUT /configs — no-op** (не reload; это mihomo-поведение), поэтому refresh = честный рестарт; refresh редкий, должен быть debounce и не пересекаться с server switch (общий lock).
- 429 / Retry-After: `next_refresh_allowed` в статусе; «Refresh unavailable — provider rate-limited, try in Ns; using cached subscription». Сырые тексты не выносить наружу.
- cache_file — runtime persistence селектора; preferred_server — manager state; после refresh — reconcile (preferred существует? выбрать; нет — AUTO).
- Security: SSL verify fail и любые сетевые ошибки — классифицированные сообщения, кэш остаётся рабочим.

## 10. Manager API v0 (Python stdlib ThreadingHTTPServer, systemd --user)

- `GET /v1/status` — единый canonical status document (schema:1, sequence, desired, network, vpn{state, effective_path, active, active_server}, servers[{id,state,latency_ms,last_check}], subscription{stale,last_refresh,next_refresh_allowed,usage,error}, last_event, operation).
- `PUT /v1/preferred {server}` → `{ok,message,status}`; `PUT /v1/mode {mode}`; `POST /v1/up {mode?}`; `POST /v1/down`; `POST /v1/refresh` (async operation); `POST /v1/network-event {state,interface,reason}` (от NM dispatcher; manager принимает, но НЕ хранит как intent).
- UI: command response = мгновенный отклик; status polling 1s пока панель видима (не 5s). Push/SSE/WS — потом, не в v0.
- Persistence: `~/.config/neodon/state.json` (только enabled/mode/preferred_server). Manager обязан быть disposable: упал — sing-box продолжает работать, systemd поднимет manager, тот реконсилит по persistent intent без рестарта VPN.

## 11. QAM UX (человеческий язык, события вместо механики)

- Норма: `● Connected · SMART`, `Server: PL-2 · 64 ms (Auto)`, `Usage: 111 / 150 GB`, кнопки [Change server][Mode][Refresh].
- Manual switch: `Connecting to DE-3…` → `✓ Connected to DE-3 · 42 ms` (оптимистичный UI, не ждать полл) или `DE-3 unavailable. Automatically selected PL-2.`
- Auto failover: `⚠ DE-3 unavailable → Finding another server…` → `✓ VPN restored. Auto: DE-3 → PL-2`; в карточке сервера видно `Preferred: DE-3 / Active: PL-2`.
- SMART total failure: `VPN unavailable. Internet is still working. Retrying automatically.` Тумблер остаётся ON (это intent).
- FULL emergency: `VPN stopped. No VPN server reachable. FULL was disabled to restore Internet. Internet is available.` Тумблер OFF (=факт).
- Server list: статусы `Connected/Healthy/Unavailable/Unknown` + пинг; никакого realtime-табло.
- Refresh — отдельный блок «Subscription»: last updated, usage, кнопка; при 429 — «Try again in Ns. Using cached subscription.»

## 12. Убираем / оставляем

Убрать (по этапам, не разом): `.transitioning` (и весь TTL-маркерный механизм), эхо-гварды UI, `.mode`+`.desired` как две истины, `singbox-server.sh` (patch+check+restart), watchdog в текущем виде, DNS, завязанный только на прокси, polling 5s как механизм управления.
Оставить: systemd (супервизор), NM dispatcher (шлёт `network-event`, не «чинит»), FULL killswitch (firewall), subscription cache, rule presets, генератор конфигов, узкий privileged helper.

## 13. Privileged helper

Вместо `sudo NOPASSWD: ALL` — узкий helper с 4–5 операциями: `firewall.apply_full / clear_full`, `dns.point_to_singbox / restore_resolved`, `network.cleanup_tun / cleanup_rules`. Helper не знает про SMART/manual/failover — только привилегированные операции.

## 14. Этапы миграции

**Phase 1 (≤1 день) — максимум эффекта, минимальный blast radius:**
1. Selector `active` (+12 нод) + URLTest `auto` + Clash API в конфигах (все три: json/full/proxy).
2. Смена сервера: вместо патча+рестарта — `PUT /proxies/active` (мгновенно, без рестарта ядра, без маркеров).
3. DNS-deadlock фикс: `dns-direct` + `dns-proxy (detour=active)` + правила; default → direct.
4. QAM: command → API → immediate read-back (без ожидания 5s-полла).
5. FULL orchestration и старый watchdog НЕ трогаем в Phase 1.
   Приёмка: смена сервера без рестарта; результат UI без ожидания полла; мёртвый сервер виден за секунды; DNS переживает смерть сервера; `.transitioning` не участвует.

**Phase 2:** singbox-manager.service (intent/lifecycle/current-path health/failover/FULL recovery/network events/status API). Приёмка: QAM и Desktop показывают один state; failover без участия UI; восстановление после сна.

**Phase 3:** удаление легаси-оркестрации (watchdog, маркеры, patch+restart, эхо-гварды, dual state). Приёмка: только manager меняет policy; только sing-box меняет outbound; только systemd управляет процессами.

**Phase 4:** subscription cleanup (rate limit, Retry-After, debounce, atomic replace, check-before-restart, post-restart reconcile). Приёмка: 429 не ломает VPN; failed refresh сохраняет прошлую подписку; preferred переживает перезапуск если существует.

**Phase 5:** DNS-cleanup (resolved vs sing-box native resolved service) — только после стабилизации SMART-роутинга.

## 15. Тест-матрица (фрагмент; полная в разделе 21 исходной раунд-таблицы)

- Серверы: healthy manual switch; dead manual switch; semilive switch; смерть активного под нагрузкой; все мёртвы; возврат preferred; manual override после failover.
- DNS: direct-домен при VPN; proxy-домен при VPN; обрыв proxy DNS; все ноды мертвы в SMART; VPN OFF; sleep/wake.
- FULL: смерть ноды; авто-recovery; все мертвы; таймаут → OFF; интернет вернулся; нет утечек direct при recovery.
- Подписка: refresh ok; malformed; SSL fail; 429; Retry-After; добавление/удаление сервера; refresh при активном VPN.
- Гонки: switch+refresh; switch+sleep; failover+manual; NM-событие при рестарте; дубликат команды; рестарт manager; крэш sing-box.

## 16. Риски

- **Квота проб URLTest**: 12 нод × 60s ≈ 17 280 проб/сутки (мелкие, но через серверы) — замерить реальный расход; при перерасходе 60s→120s.
- **URLTest stale/first-outbound fallback** при тотале — поэтому total-failure это always manager.
- **Manual switch latency**: не полагаться на интервал urltest для ручного выбора — selector switch + немедленная end-to-end валидация.
- **Sleep**: NETWORK_DOWN не равно VPN failure; заморозка решений + reconcile после.
- **Config restart race**: refresh — единственный плановый рестарт ядра; общий lock, check-before-restart, reconcile после.
- **Проверить при внедрении (не подтверждено нашим билдом)**: синтаксис DNS rules 1.14 (action=route), листенер DNS на 127.0.0.1:53, `GET/DELETE /connections`, поведение urltest с полуживыми нодами, факт no-op PUT /configs.

## 17. Открытые вопросы

- Окно FULL recovery N минут (предложение: 5).
- Каденция current-path probe: 5s vs 10s.
- Реальный расход квоты URLTest 60s vs 120s.
- Судьба systemd-resolved (Phase 5).
- Расхождение Usage с внешней панелью провайдера/другим устройством владельца.
- Семантика при исчезновении preferred_server из подписки.

## 18. Связь с текущим состоянием (04.10.2026)

- Спека `035-panel-switch-ux` (деплой 04.10): pending-индикация, friendly-статусы, ретрай-тап, TTL 12с, ранняя запись selected — **временный мост** до v2; её UX-принципы (события вместо механики, оптимистичный отклик) входят в целевой дизайн.
- Реализация Phase 1 затрагивает: генератор конфигов (12 нод + группы), `singbox-toggle/server` (замена механики смены сервера), DNS-блок конфигов, панель (read-back). Всё с бэкапами и живой приёмкой.
