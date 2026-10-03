# Готовые VPN-плагины для Decky Loader — ресёрч под neodon-vpn

**Дата:** 2026-10-04 · **Устройство-цель:** ROG Ally X, CachyOS, Game Mode, Decky Loader v3.2.x
**Вопрос:** может ли готовый плагин закрыть «ссылка-подписка → рабочий VPN в Game Mode», и что перенять в свой плагин.

**Метод:** `webstack ready-made` (gate), `webstack decky` (официальный стор, 110 плагинов), GitHub REST API + `webstack github` для зрелости. Все факты — с URL и датами. Устройство не трогалось.

> **Покрытие:** Decky store (JSON, 110 плагинов) ✅ · GitHub repo/code-search ✅ · GitHub REST (звёзды/релизы/issues/даты) ✅ · README кандидатов ✅ · Reddit/YT (ready-made gate) ✅
> **Misses:** gh-search через `gh auth`-с-токеном завис (git credential fill) — заменён на прямой GitHub API; code-grep grep.app не потребовался (поведение читалось из README/исходников).

---

## 1. Каталог официального стора (plugins.deckbrew.xyz/plugins)

Всего **110 плагинов**. После фильтра по VPN/сетевой тематике (`vpn`, `proxy`, `xray`, `sing-box`, `clash`, `mihomo`, `wireguard`, `tunnel`, `shadowsocks`, `zerotier`, `dns`, `spoofdpi`) — **11 совпадений**. Из них реальные VPN/прокси-плагины — 4 (см. таблицу); остальные — DNS/WiFi/файловый сервер (не VPN).

**Ключевой факт:** в официальном сторе **нет ни одного плагина, который умеет принимать ссылку-подписку** (vless/xray/sing-box auto-config). Все subscription-клиенты (xray-decky, DeckyClash, hiddify) — в сторе НЕ опубликованы, ставятся вручную (ZIP/gh). Стор содержит только ручные конфиги.

---

## 2. Таблица кандидатов

| Плагин | Ссылка | Подход / движок | Подписка (ссылка → работает)? | Зрелость / дата (2026) | Game Mode | Вердикт |
|---|---|---|---|---|---|---|
| **xray-decky** | github.com/VadimOnix/xray-decky | sing-box + Xray-ядра; VLESS/REALITY/VMess/Trojan/SS/Hysteria2/TUIC; **TUN-режим**, kill switch, веб-панель | **ДА** — «import a subscription URL (base64 or plain-text link lists) and refresh in place», показ квоты/срока из `Subscription-Userinfo` | 23★, 3 форка, MIT, **создан 2026-01-26, релиз v2.3.2 2026-08-13, последний push 2026-09-16**, 2 открытых issue | **ДА** — «TUN mode for Gaming Mode»; явно описано, что SOCKS не покрывает игры | **Лучший арх.-матч.** Единственный с явным TUN+подпиской+веб-панелью+kill switch. Зрелость средняя. |
| **b-ostrov/hiddify-steam-deck-vpn** | github.com/b-ostrov/hiddify-steam-deck-vpn | **sing-box**; VLESS/REALITY/VMess/Trojan/SS/Hysteria2/TUIC; отдельно десктоп-клиент Hiddify + Decky-плагин | **ДА** — «subscription server updates directly from the Decky plugin», hot-apply через Clash API без разрыва TUN | 30★, **без лицензии**, создан 2026-03-21, релиз v1.3.18 2026-08-19, **последний push 2026-10-03 (вчера!)**, 0 открытых issue | **ДА** — «VPN control ... without leaving Game Mode»; профили/выбор сервера в Game Mode | **Самый живой.** Активнейшая разработка. Минус: нет лицензии, зависимость от апстрима Hiddify. |
| **DeckyClash** | github.com/chenx-dust/DeckyClash (в сторе: «Decky Clash», id 115) | **Clash/Mihomo** (MetaCubeX/mihomo ядро внутри) | **ДА** — «out of the box, with subscriptions importer»; импорт подписок Clash-формата | **392★**, 13 форков, BSD-3, создан 2025-12-14, релиз v1.2.1 2026-02-22, **последний push 2026-09-28**, 1 открытый issue; **в официальном сторе, 10 832 загрузки** | ДА (SteamOS; Clash TUN) — но README акцент на Desktop/TUN без явного «Game Mode» маркетинга | **Самый зрелый и в сторе.** Но экосистема **Clash**, а не vless-подписка провайдера: нужен Clash-yaml, не «вставил vless-ссылку». |
| **b-ostrov/decky-hiddify** | github.com/b-ostrov/decky-hiddify | Hiddify/sing-box, тонкий контрол-плагин | ДА (через Hiddify-профиль) | 3★, создан 2026-03-21, **последний push 2026-03-22 — заброшен** (v1.2.0) | ДА | Устаревший предшественник hiddify-steam-deck-vpn. Не брать. |
| **ShadowDeck** | plugins.deckbrew.xyz → ShadowDeck (id 129) | Shadowsocks (ручной) | **НЕТ** — только ручной Shadowsocks | 1400 загрузок, v1.1.11 2026-03-13, **последний релиз 2026-03-13** | unclear | Нишевый SS-only, подписки нет. Мимо. |
| **Decky Clash** (store-версия) | там же | см. DeckyClash выше | ДА (Clash-подписки) | 2026-02-22 в сторе | ДА | См. DeckyClash. |
| **Decky-SpoofDPI** | plugins.deckbrew.xyz (id 95) | DPI-обход (SpoofDPI), НЕ VPN | НЕТ | 8216 загрузок, **2025-02-05 — устарел** | ДА | Не VPN-туннель. Только обход DPI. |
| **Decky Zerotier** | plugins.deckbrew.xyz (id 99) | ZeroTier SD-WAN | НЕТ (сети ZeroTier, не подписка) | 6297 загрузок, **2025-03-04 — устарел** | ДА | Не подписочный провайдер-VPN. |

---

## 3. Проверка кандидатов из сентябрьского ресёрча (актуальность в 2026)

### TunnelDeck (steve228uk/TunnelDeck) — актуален как проект, но НЕ решает нашу задачу
- **167★**, 17 форков, создан 2023-03-17. **Последний push 2024-05-26** (по API), но `updated_at` = **2026-10-01** (обновления метаданных, не кода). **Релиз v1.0.4 от 2024-10-22** — новых релизов нет ~2 года.
- **Стор:** id 30, **80 138 загрузок** (лидер стора), последнее обновление **2024-10-22**.
- **Подход:** OpenVPN/WireGuard **через NetworkManager**; конфиг готовится **вручную в Desktop Mode** (импорт `.conf`/`.ovpn`), плагин лишь включает/выключает готовые соединения; root-устанавливает OpenVPN как systemd-sysext.
- **Подписка?** **НЕТ.** Connect требует предварительной настройки в Desktop Mode. Это ровно тот ручной путь, которого мы избегаем.
- **Вердикт:** жив как «переключатель NetworkManager-VPN», но **не закрывает «ссылка-подписка → работает»** и по коду статичен с 2024. Для наших целей — не конкурент, но ценен как источник паттернов (см. §4).

### vpn-deck (MrWaip/vpn-deck) — актуален и активен, но про AmneziaWG, не про подписку
- **53★**, 3 форка, создан ~2026, **последний push 2026-09-26**, релиз v2.x.
- **Подход:** **AmneziaWG** (обфусцированный WireGuard), **требует root**, работает через `awg-quick`, конфиги `vd-<name>`, симлинки в `/etc/amnezia/amneziawg/`; бинарники (amneziawg-go, awg, awg-quick) **включены в релиз**. DNS-шим `resolvconf` через systemd-resolved.
- **Подписка?** **НЕТ.** Импорт **`.conf`-файла** и `vpn://`-конфигов вручную. v2 убрал управление `awg0` (только свои `vd-*` интерфейсы).
- **Вердикт:** **актуален в 2026** (обновлялся 2026-09-26), качественно сделан для AmneziaWG. Но это **не подписочный клиент**: провайдерская vless/xray-ссылка не подойдёт, нужен готовый `.conf`. Для «вставил ссылку» — не подходит; для AmneziaWG-юзкейса — референс №1.

---

## 4. Что перенять в neodon-vpn

Инженерные паттерны (с доказательствами из исходников/README):

1. **Жизненный цикл VPN-сервиса независимо от QAM-панели (главное).**
   - **hiddify-steam-deck-vpn:** sing-box держит TUN и перезагружается через **Clash API без разрыва туннеля** — «sing-box reloads via its Clash API without tearing down the TUN interface». Панель QAM — тонкий контрол, ядро живёт само. → Перенимаем: backend sing-box как systemd-юнит/демон, QAM лишь подаёт команды start/stop/switch.
   - **vpn-deck:** интерфейсы `vd-<name>` + симлинки + root-обёртки вокруг `awg-quick`; состояние переживает закрытие панели.
   - **TunnelDeck:** соединения — объекты NetworkManager, плагин только тогглит их → состояние принадлежит системе, не UI.

2. **Root-модель.** Все три требуют root; чистый путь — **pre-built бинарники ядра в релизе** (vpn-deck включает amneziawg-go/awg/awg-quick; hiddify — самораспаковывающийся installer) вместо сборки на устройстве. У нас уже есть `polkit/` и `flags/` — сверить: избегаем запроса sudo из UI.

3. **TUN обязателен для Game Mode.** xray-decky прямо документирует: «In Gaming Mode, Steam does not respect system SOCKS proxy settings — games and most system services ignore it. TUN mode ... the only reliable way». Kill switch тоже только с TUN. → Наш плагин должен строить **TUN**, а не SOCKS.

4. **Подписка + hot-apply.** Паттерн hiddify: рефреш подписки через активный tun0 и **горячее применение новых серверов без разрыва**; показ квоты/срока из `Subscription-Userinfo` (как в xray-decky). → Перенимаем: импорт base64/plain-ссылок, refresh in place, показ лимита трафика.

5. **Веб-панель как второй пульт** (xray-decky): Steam-стилизованная админка по QR с телефона/ПК — управление/статус/список серверов/подписка/kill switch. Полезно как fallback и как «CLI-точка входа» без GUI (когда кнопка QAM мертва из-за кэша Steam).

6. **НЕ перенимать:** Clash-yaml-формат как основной (DeckyClash зрел и популярен, но наш провайдер даёт vless-ссылки, а не Clash-конфиги); DPI-обход вместо туннеля (SpoofDPI); ZeroTier (не тот класс).

---

## 5. Итог

**Готовый плагин в принципе может закрыть потребность, но ни один не сочетает всё сразу:**

- **Закрывает «ссылка-подписка → Game Mode» лучше всех — `xray-decky`** (единственный с явными «subscription URL» + TUN для Game Mode + kill switch + веб-панель). **Но:** вне официального стора (ставится ZIP/gh вручную), зрелость средняя (23★, ~9 мес. истории, 2 открытых issue), вся логика — в одном плагине (нет гарантии, что сервис переживёт закрытие QAM так же чисто, как у hiddify).
- **Самый живой и с лучшим hot-apply — `hiddify-steam-deck-vpn`** (push вчера, 0 открытых issue, «ждёт обновления без разрыва TUN»), но зависит от апстрима Hiddify и **без лицензии** (риск для форка/встраивания).
- **Самый зрелый и в сторе — `DeckyClash`** (392★), но это Clash/Mihomo-экосистема: провайдерскую vless-ссылку он не проглотит без Clash-yaml.
- **Из сентябрьских:** `TunnelDeck` (167★, 80k загрузок) — только NetworkManager/ручной конфиг, код статичен с 2024 → «ссылка → работает» НЕ закрывает. `vpn-deck` (53★, обновлён 2026-09-26) — живой AmneziaWG-менеджер, но тоже `.conf` вручную, не подписка.

**Рекомендация:** свой плагин делаем — задача не закрыта ни одним готовым решением целиком. Архитектурный референс — **связка `hiddify-steam-deck-vpn` (жизненный цикл сервиса + hot-apply подписки) + `xray-decky` (TUN, kill switch, веб-панель, показ квоты)**. Наш козырь = **официальное присутствие в сторе + поддержка именно vless-подписок в один вставленный URL + polkit-модель без ручного sudo** — этого сочетания нет ни у одного кандидата.

---

### Sources (URL + что взято)
- plugins.deckbrew.xyz/plugins — JSON-каталог, 110 плагинов, теги/загрузки/даты (fetched 2026-10-04).
- github.com/VadimOnix/xray-decky — подписки/TUN/веб-панель; API: 23★, MIT, v2.3.2 2026-08-13, push 2026-09-16.
- github.com/b-ostrov/hiddify-steam-deck-vpn — sing-box, subscription hot-apply; API: 30★, push 2026-10-03, релиз v1.3.18 2026-08-19.
- github.com/chenx-dust/DeckyClash — Mihomo-ядро, importer подписок; API: 392★, BSD-3, v1.2.1 2026-02-22, push 2026-09-28.
- github.com/steve228uk/TunnelDeck — NetworkManager/OpenVPN/WireGuard, ручная настройка; API: 167★, релиз v1.0.4 2024-10-22.
- github.com/MrWaip/vpn-deck — AmneziaWG, root, awg-quick; API: 53★, push 2026-09-26.
- github.com/Algorithm0/AmneziaVPN-DeckyLoader — новый (2026-09-28), 1★, v0.1.0 — сырой.
- Стор: ShadowDeck id129 (2026-03-13), Decky-SpoofDPI id95 (2025-02-05), Decky Zerotier id99 (2025-03-04), TunnelDeck id30 (2024-10-22).
