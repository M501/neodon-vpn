# Bazzite — Neodon VPN (v2RayTun-клон для Linux)

> **Статус 2026-08-28 19:48 — VERIFIED 21/21 PASS (Gaming Mode):** хост восстановлен полностью (см. `state/CURRENT.md` §2026-08-28). До этого 2026-08-25 хост был пуст/offline — см. ниже. хост восстановлен после переустановки Bazzite 43 → `~/AI` пуст, весь рабочий стек на SD `/run/media/m26/0000-D182/neodon-vpn` (58M `sing-box 1.13.18` + `neodon-vpn.py` + `singbox-toggle/server/killswitch/hostctl`). Хост оффлайн на момент документа (Wi-Fi/Tailscale нет связи) — восстановление детерминированное, скрипты готовы, тесты без пароля — критерий готовности.

## Что это

Neodon — персональный VPN-клиент для Bazzite Linux, семантика **v2RayTun** (Windows/Android) на `sing-box 1.13.18` + PySide6 GUI.

```
PySide6 GUI (Flatpak) ──► neodon-hostctl (whitelist) ──► singbox-toggle.sh / singbox-server.sh
                                                        ──► systemd --user (3 юнита)
                                                             ──► sing-box engine
                                                                  ├─ PROXY  → 127.0.0.1:10808 (smart, без TUN)
                                                                  └─ TUNNEL → tun0 + killswitch (ядерный)
```

**Модель пользователя — только это:**

```
OFF / ON + [ PROXY | TUNNEL ]
```

Нет режимов `SOCKS5`, `SMART`, `FULL` в GUI — это внутренние имена (`smart`→PROXY, `full`→TUNNEL). `SOCKS5` остаётся транспортом внутри PROXY, но не показывается как выбор.

## Где что лежит

### SD-карта (единственный бэкап, беречь от записи)

```
/run/media/m26/0000-D182/neodon-vpn/
├── neodon-vpn.py          63KB 1487 строк — GUI (OFF|PROXY|TUNNEL)
├── app/neodon-vpn.py      дубликат + flags/ + desktop/svg + gui-state/action.json
├── singbox-toggle.sh      211 строк — канонический переключатель
├── singbox-server.sh      149 строк — выбор сервера
├── killswitch.sh          143 строки — fail-closed firewalld direct
├── neodon-hostctl         51 строка — whitelist bridge
├── neodon-sub.py          137 строк — подписка u.neodon.net/c/… (UA v2rayN/7.24.6)
├── sing-box               58M  sha 8cb29c5b  (1.13.18, pinned)
├── flags/*.png            7 флагов
├── io.neodon.gui.json     Flatpak manifest (org.kde.Platform 6.11)
└── README.md, .gitignore
```

**Чего нет на SD** (живёт в `~/AI/singbox` по дизайну): `config.json / config-full.json / config-proxy.json`, `apply-profile.py`, `geosite.db`, `*.srs`, `profiles/*.json`, `selected-server.json`, `.mode`, `watchdog-state.json`, systemd юниты, sudoers/polkit.

### Хост после переустановки (2026-08-25)

```
~/AI/                         — отсутствует (требует восстановления)
~/.config/systemd/user/       — отсутствует
/etc/sudoers.d/               — пуст (total 0)
/etc/polkit-1/rules.d/        — только 49-polkit-pkla-compat.rules
/usr/local/bin/sing-box       — отсутствует
firewalld                     — active, zone FedoraWorkstation, 0 direct rules
flatpak io.neodon.gui         — не установлен
```

После восстановления:

```
~/AI/singbox/
  config.json                 smart (mixed 10808 + tun auto_route)
  config-full.json            full/tunnel (tun0 only, без профилей)
  config-proxy.json           proxy (mixed 10808 only, без tun)
  selected-server.json        {"tag","server","server_port","updated"}
  .mode                       desired mode (smart/full/proxy/off)
  .profile                    active profile id
  .transitioning              маркер TRANSITIONING
  .toggle.lock                flock мьютекс
  watchdog-state.json         {consecutive_failures, backoff_index, next_due_ts, watchdog_status}
  killswitch.sh               (копия с SD, +x)
  singbox-toggle.sh           (канонический, +x)
  singbox-server.sh           (+x)
  apply-profile.py            профили → route.rules
  profiles/*.json             8 пресетов + default/ai/anti-censorship
  geosite-*.srs / geoip-*.srs rule_set (local, format source)
  subscription-manager.py     (опционально)

~/AI/neodon-vpn/
  neodon-vpn.py               GUI (Flatpak: /app/bin/neodon-vpn.py)
  gui-state.json / gui-action.json
  flags/

~/AI/neodon-hostctl           host bridge (~/AI/singbox-toggle.sh + singbox-server.sh)
~/AI/neodon-sub/neodon-sub.py подписка (RAW ~/AI/neodon-sub/raw.json)
~/.config/systemd/user/
  sing-box.service            smart  → sing-box run -c ~/AI/singbox/config.json
  sing-box-proxy.service      proxy  → config-proxy.json
  sing-box-full.service       full   → config-full.json (с killswitch)
  neodon-boot.service         oneshot автозапуск (smart, WantedBy=default.target)
/etc/sudoers.d/90-singbox-killswitch
/etc/polkit-1/rules.d/50-singbox-resolve.rules
/usr/local/bin/sing-box       58M + cap_net_admin,cap_net_raw+ep
```

## PROXY vs TUNNEL — что должен делать

### PROXY (умный, дефолт пользователя)

- Без TUN, без глобального killswitch.
- `sing-box-proxy.service` → mixed inbound `127.0.0.1:10808` (SOCKS5+HTTP).
- Firefox auto-proxy: `firefox-proxy.sh apply` пишет в `~/.var/app/org.mozilla.firefox/.mozilla/firefox/*/prefs.js` (fallback `~/.mozilla/firefox/*/prefs.js`):
  ```
  network.proxy.type=1
  network.proxy.socks=127.0.0.1
  network.proxy.socks_port=10808
  network.proxy.socks_remote_dns=true
  network.proxy.share_proxy_settings=true
  ```
  При OFF/TUNNEL → `firefox-proxy.sh restore` из `.bak`.
- Routing внутри sing-box (smart): `sniff` + `hijack-dns` + `geoip-private→direct` + `qbittorrent/steam/steamwebhelper/reaper→direct` + `ozon.ru→direct` + `bittorrent→direct` + **preset rules** + `geoip-ru/geosite-ru→direct` → `final: proxy|direct`.
- На практике:
  - qBittorrent / Steam → **ISP DIRECT** (не жрёт квоту, `ss` покажет wlan0)
  - YouTube → **VPN** (через 10808)
  - Ozon (`ozon.ru`) → **DIRECT** (иначе детектит VPN и не открывается)
  - Amazon Marketplace → **DIRECT** (по preset)
  - Остальное — по выбранному пресету.
- Не-прокси приложения (не используют 10808) → ISP DIRECT.
- Проверка: `curl -x socks5h://127.0.0.1:10808 https://api.ipify.org` → VPN IP, `curl https://api.ipify.org` → ISP `79.139.*`, `journalctl -u sing-box-proxy | grep outbound`.

### TUNNEL (ядерный, весь трафик через VPN)

- `sing-box-full.service` → TUN `tun0` (`172.19.0.1/30`, `auto_route`, `strict_route=false`).
- После `systemctl --user start sing-box-full.service` (ждать до 15s `is-active`) → проверить `ip link show tun0` + `ip route get 1.1.1.1 | grep tun0` → **`killswitch.sh install`** (резолв endpoint IPs **пока DNS открыт**, `add-missing` без flush, verify count, **REJECT prio 20 LAST**). Любая ошибка → `exit 1`, firewall остаётся **LOCKED fail-closed**.
- `firefox-proxy.sh restore` перед стартом (сброс прокси).
- Игнорирует выбранный профиль by design (`config-full.json` не трогается `apply-profile.py`; `md5sum config-full.json` до/после `apply-profile` совпадает).
- На практике: **всё** через VPN, включая qBittorrent/Steam/Ozon. Квота жрётся, но работают Codex Desktop / игры / драйверы которые не уважают прокси.
- Killswitch allowlist (prio): `lo(0)`, `tun0(1)`, `192.168/16|10/8|172.16/12|fc00::/7|fe80::/10(2)`, `DHCP sport 68/546(3)`, `ICMPv6 133/135/136(3)`, `1.1.1.1|1.0.0.1(4)`, **endpoint IPs(5)** (`getent ahostsv4 <server>` + `u.neodon.net`), **REJECT(20)**. `verify` — каждый expected rule должен присутствовать.
- Fail-closed: `TUNNEL desired=ON + sing-box crash → firewall LOCKED → интернет не падает на ISP → recovery/restart → VPN восстановлен`. Только явный `OFF` снимает lock (`killswitch.sh remove` → `remove-rules OUTPUT_direct`).

## Community presets (8 + 3 legacy)

Генерация: `gen_profiles.py` → `profiles_out/*.json` (уже готовы) → `upload_profiles.py` (копирует в `~/AI/singbox/profiles/`, регистрирует `.srs`, расширяет `apply-profile.py PROFILES` + `neodon-hostctl` whitelist, `--check` каждый).

| id | final | логика |
|---|---|---|
| `default` | proxy | RU/торренты/Steam/Ozon DIRECT, остальное VPN |
| `ru-bez-vpn` | proxy | + avito.st, category-ru, `*.ru`, `*.xn--p1ai` → DIRECT |
| `russia-mimo` | proxy | + private, `*.ru`, `*.xn--p1ai` → DIRECT |
| `ru-traffic-direct` | proxy | + avito.st, vk.com, category-ru, `*.ru`, `*.su` → DIRECT |
| `popular-ai` | direct | `category-ai-!cn`, `category-ai-cn` → PROXY |
| `social-networks` | direct | discord, github, google, meta, openai, spotify, telegram, tiktok, vk, whatsapp → PROXY |
| `only-unavailable` | direct | anime, anthropic, artstation, discord, google-gemini, instagram, linkedin, meta, microsoft, notion, openai, soundcloud, speedtest, spotify, tiktok, twitch, twitter, youtube → PROXY |
| `socseti-vpn` | direct | discord, google, instagram, openai, spotify, telegram, tiktok, whatsapp, youtube → PROXY |
| `basic-set` | direct | 1e100.net, bcvcdn.com, cdninstagram, chatgpt.com, discord.*, fbcdn.net, googlevideo.com, instagram.com, tiktok.tv, twitch.tv, whatsapp, youtube.com, ytimg.com, cloudflare, discord, meta, openai, telegram, tiktok, whatsapp, youtube → PROXY |

Каждый добавляет `BASE_HARD` (sniff, hijack-dns, geoip-private, qbittorrent/steam, ozon.ru, bittorrent → DIRECT) + `BASE_RU` (geoip-ru, geosite-ru → DIRECT). `final` = куда уходит unmatched. `geosite-*` → `.srs` (`sing-box geosite export tag -o geosite-tag.srs`, `format: source`, зарегистрированы в `route.rule_set`).

Legacy `ai`, `anti-censorship` — остаются (файлы на хосте, SKIP при генерации).

Применение:

```bash
python3 ~/AI/singbox/apply-profile.py <id>          # validate → sing-box check → backup → atomic apply → restart → health → rollback on fail
python3 ~/AI/singbox/apply-profile.py --check <id>  # только validate + check, без коммита
neodon-hostctl profile <id>                         # через host bridge (Flatpak: flatpak-spawn --host neodon-hostctl profile <id>)
```

`TUNNEL` не трогает `config-full.json` — инвариант: `md5sum config-full.json` до/после `apply-profile` совпадает.

## Passwordless — ни одного запроса пароля

**Критерий из ТЗ:** ни переключение серверов, ни `PROXY|TUNNEL`, ни вкл/выкл не спрашивают `sudo` пароль — ни на какой стадии.

| Компонент | Почему без пароля |
|---|---|
| `systemctl --user start/stop` | user-сервисы, не требуют sudo |
| `sing-box run` (TUN) | `setcap cap_net_admin,cap_net_raw+ep /usr/local/bin/sing-box` → создание tun0 без sudo, `getcap` должен показать `cap_net_admin` |
| `firewall-cmd --direct --{get,add,remove}-rules` | `sudo -n` (non-interactive) + `/etc/sudoers.d/90-singbox-killswitch`: `m26 ALL=(ALL) NOPASSWD: /usr/bin/firewall-cmd --direct *` (`visudo -c` валиден). Без правила — `sudo -n` молча падает, GUI не виснет с промптом |
| `firefox-proxy.sh apply/restore` | работает в `$HOME`, без sudo |
| `neodon-hostctl` | whitelist, сам вызывает `sudo -n` только для firewall |
| `status-json` | `sudo -n firewall-cmd --direct --get-all-rules | wc -l` уже NOPASSWD, остальное без sudo |

Polkit fallback: `/etc/polkit-1/rules.d/50-singbox-resolve.rules` (JS) разрешает `org.fedoraproject.FirewallD1.*` для `unix-user:m26` без auth — если polkit не сработает, sudoers уже покрывает.

Проверка:

```bash
sudo -n true && echo OK || echo FAIL          # должен быть OK
sudo -n firewall-cmd --direct --get-all-rules | wc -l   # без пароля
getcap /usr/local/bin/sing-box | grep cap_net_admin
```

## Команды

```bash
# CLI (хост)
~/AI/neodon-hostctl status                    # JSON: desired_mode, actual_state, service, firewall_rules, tun0, exit_ip, server_tag, latency_ms, watchdog_status
~/AI/neodon-hostctl start proxy               # PROXY ON (smart)
~/AI/neodon-hostctl start full                # TUNNEL ON (full, с killswitch)
~/AI/neodon-hostctl stop                      # OFF (снимает firewall, restore firefox)
~/AI/neodon-hostctl retry                     # повтор desired mode (читает .mode)
~/AI/neodon-hostctl server 1                  # NL (список: ~/AI/singbox-server.sh list)
neodon-hostctl profile popular-ai             # смена пресета
bash ~/AI/singbox-toggle.sh status-json       # то же что status, но напрямую
bash ~/AI/singbox-server.sh list              # список серверов из raw.json
bash ~/AI/singbox/killswitch.sh verify        # проверить каждый expected rule
bash ~/AI/singbox/killswitch.sh install       # установить (fail-fast)
bash ~/AI/singbox/killswitch.sh remove        # снять (idempotent)

# GUI
flatpak run io.neodon.gui                     # главный экран: таймер + питание + PROXY|TUNNEL + Traffic rules + серверы
python3 ~/AI/neodon-vpn/neodon-vpn.py         # вне Flatpak (для теста)

# Подписка
python3 ~/AI/neodon-sub/neodon-sub.py         # fetch raw.json + sub.txt (base64 links)
curl -s http://127.0.0.1:18080/sub   # локальный HTTP подписки (если запущен neodon-sub.py как сервис)
```

## Установка с SD (после переустановки Bazzite)

> Хост 2026-08-25 чистый (`~/AI` нет). SD — единственный источник (копировать, не перемещать).

```bash
# 0. SD смонтирована в /run/media/m26/0000-D182 (vfat, 860M свободно)
ls /run/media/m26/0000-D182/neodon-vpn/sing-box  # 58M должен быть виден

# 1. Копирование SD → Host
mkdir -p ~/AI/neodon-vpn ~/AI/singbox ~/AI/neodon-sub ~/.config/systemd/user
cp -a /run/media/m26/0000-D182/neodon-vpn/sing-box /tmp/sing-box
sudo cp /tmp/sing-box /usr/local/bin/sing-box && sudo chmod +x /usr/local/bin/sing-box
cp -a /run/media/m26/0000-D182/neodon-vpn/neodon-hostctl ~/AI/neodon-hostctl
cp -a /run/media/m26/0000-D182/neodon-vpn/singbox-toggle.sh ~/AI/singbox/singbox-toggle.sh
cp -a /run/media/m26/0000-D182/neodon-vpn/singbox-server.sh ~/AI/singbox/singbox-server.sh
cp -a /run/media/m26/0000-D182/neodon-vpn/killswitch.sh ~/AI/singbox/killswitch.sh
cp -a /run/media/m26/0000-D182/neodon-vpn/neodon-sub.py ~/AI/neodon-sub/neodon-sub.py
cp -a /run/media/m26/0000-D182/neodon-vpn/neodon-vpn.py ~/AI/neodon-vpn/neodon-vpn.py
cp -a /run/media/m26/0000-D182/neodon-vpn/app ~/AI/neodon-vpn/app 2>/dev/null || true
cp -a /run/media/m26/0000-D182/neodon-vpn/flags ~/AI/neodon-vpn/flags 2>/dev/null || true
cp -a /run/media/m26/0000-D182/neodon-vpn/io.neodon.gui.json ~/AI/neodon-vpn/io.neodon.gui.json
# firefox-proxy.sh берём из хелперов (на SD его нет):
cp -a ~/.hermes-ssh/firefox-proxy.sh ~/AI/neodon-flatpak/firefox-proxy.sh  # или ~/AI/singbox/
chmod +x ~/AI/neodon-hostctl ~/AI/singbox/*.sh ~/AI/neodon-sub/*.py

# 2. Capabilities + sudoers/polkit (passwordless)
sudo setcap cap_net_admin,cap_net_raw+ep /usr/local/bin/sing-box
echo 'm26 ALL=(ALL) NOPASSWD: /usr/bin/firewall-cmd --direct *' | sudo tee /etc/sudoers.d/90-singbox-killswitch
sudo chmod 440 /etc/sudoers.d/90-singbox-killswitch && sudo visudo -c
# polkit (Fedora 43, polkit 124):
sudo tee /etc/polkit-1/rules.d/50-singbox-resolve.rules >/dev/null <<'RULE'
polkit.addRule(function(a,s){ if(a.id.indexOf("org.fedoraproject.FirewallD1.")==0 && s.user=="m26") return polkit.Result.YES; });
RULE

# 3. Реконструкция sing-box конфигов (шаблон + подписка)
# 3a. geosite.db / geoip.db — если нет, скачать из sing-box release или взять из бэкапа
# 3b. config.json / config-full.json / config-proxy.json — сгенерировать из шаблона (см. gen_profiles + export_rule_sets)
# 3c. profiles — скопировать готовые:
mkdir -p ~/AI/singbox/profiles
cp -a ~/.hermes-ssh/profiles_out/*.json ~/AI/singbox/profiles/
# 3d. rule_set .srs:
python3 ~/.hermes-ssh/export_rule_sets.py   # экспортирует geosite-*.srs и регистрирует в route.rule_set
# 3e. подписка:
python3 ~/AI/neodon-sub/neodon-sub.py       # fetch raw.json (если сеть доступна; без VPN — прямой fetch)

# 4. systemd --user
cat > ~/.config/systemd/user/sing-box.service <<'UNIT'
[Unit]
Description=Neodon VPN (smart/proxy)
After=network-online.target
Wants=network-online.target
[Service]
Type=simple
ExecStart=/usr/local/bin/sing-box run -c %h/AI/singbox/config.json
Restart=on-failure
RestartSec=3
[Install]
WantedBy=default.target
UNIT
cat > ~/.config/systemd/user/sing-box-full.service <<'UNIT'
[Unit]
Description=Neodon VPN (full/tunnel)
After=network-online.target
Wants=network-online.target
[Service]
Type=simple
ExecStart=/usr/local/bin/sing-box run -c %h/AI/singbox/config-full.json
Restart=on-failure
RestartSec=3
[Install]
WantedBy=default.target
UNIT
cat > ~/.config/systemd/user/sing-box-proxy.service <<'UNIT'
[Unit]
Description=Neodon VPN (proxy only)
After=network-online.target
Wants=network-online.target
[Service]
Type=simple
ExecStart=/usr/local/bin/sing-box run -c %h/AI/singbox/config-proxy.json
Restart=on-failure
RestartSec=3
[Install]
WantedBy=default.target
UNIT
cat > ~/.config/systemd/user/neodon-boot.service <<'UNIT'
[Unit]
Description=Neodon VPN autostart
After=network-online.target sing-box.service
[Service]
Type=oneshot
ExecStart=%h/AI/singbox/singbox-toggle.sh smart
RemainAfterExit=yes
[Install]
WantedBy=default.target
UNIT
systemctl --user daemon-reload
systemctl --user enable neodon-boot.service sing-box.service sing-box-full.service sing-box-proxy.service

# 5. Проверка без пароля
sudo -n firewall-cmd --direct --get-all-rules | wc -l   # 0 без туннеля
~/AI/neodon-hostctl status | python3 -m json.tool
~/AI/neodon-hostctl start proxy && sleep 4 && ~/AI/neodon-hostctl status | python3 -m json.tool
curl -x socks5h://127.0.0.1:10808 -s -m 5 https://api.ipify.org; echo " via proxy"
~/AI/neodon-hostctl start full && sleep 8 && ~/AI/neodon-hostctl status | python3 -m json.tool
ip link show tun0 && sudo -n firewall-cmd --direct --get-all-rules | wc -l
~/AI/neodon-hostctl stop && ~/AI/neodon-hostctl status | python3 -m json.tool

# 6. Flatpak GUI (опционально, если нужен)
# cd ~/AI/neodon-vpn && flatpak run org.flatpak.Builder --user --force-clean --repo=repo builddir io.neodon.gui.json
# flatpak install --user repo io.neodon.gui
# flatpak run io.neodon.gui
```

## Touchscreen (Ally X, 2026-08-29)

- `QScroller` на оба `QScrollArea` (`LeftMouseButtonGesture` + `TouchGesture`, delay 0.08, distance 0.008-0.01, smoothing 0.25, deceleration 0.12) — тяни пальцем в любом месте страницы.
- Запуск через `systemd-run --user neodon-gui` (наследует `WAYLAND_DISPLAY=wayland-0`)
- `offscreen`/`wayland` rc0, `pgrep` single-instance.

## Траблшутинг

| Симптом | Что делать |
|---|---|
| `LOCKED` (Protected — VPN unavailable) | Только `neodon-hostctl stop` снимает lock (fail-closed). Не `reboot` — firewall в direct rules, переживёт рестарт sing-box |
| `tun0 missing` / `no tun0 route` в FULL | `getcap /usr/local/bin/sing-box` должен показать `cap_net_admin`; `sing-box check -c ~/AI/singbox/config-full.json` должен пройти; `journalctl --user -u sing-box-full -n 100` |
| `PROXY` не берёт Firefox | `cat ~/.var/app/org.mozilla.firefox/.mozilla/firefox/*/prefs.js | grep proxy` должен показать `socks 127.0.0.1:10808`; если нет — `bash ~/AI/neodon-flatpak/firefox-proxy.sh apply` вручную, проверить `prefs.js.neodon.bak` |
| `sudo -n firewall-cmd` просит пароль | `cat /etc/sudoers.d/90-singbox-killswitch` должен быть `m26 ALL=(ALL) NOPASSWD: /usr/bin/firewall-cmd --direct *` + `visudo -c` OK; `sudo -n true && echo OK` |
| `social-networks` не применяется | `python3 ~/AI/singbox/apply-profile.py --check social-networks` должен показать `check passed`; `journalctl --user -u sing-box -n 50 | grep outbound` |
| Подписка `raw.json` пустая | `python3 ~/AI/neodon-sub/neodon-sub.py` (прямой fetch без VPN); если URL недоступен — проверить `grep URL ~/AI/neodon-sub/neodon-sub.py` |
| Bazzite rebase затирает `/etc` | `sudoers.d`/`polkit` живут в `/etc` (persist в ostree `/etc` overlay) — переживают rebase, но проверить после `rpm-ostree rebase` |

## Тесты — как проверяем что всё работает без пароля

Детерминированный пакет (каждый тест — без `echo пароль | sudo -S`, только `sudo -n` внутри скриптов):

```
1. OFF status — без пароля, state=OFF, firewall 0, tun0 absent
2. PROXY ON — без пароля, state=CONNECTED, 10808 LISTEN, curl via proxy → VPN IP
3. PROXY server switch — без пароля, server_tag меняется, sing-box restart
4. TUNNEL ON — без пароля, tun0 present, firewall ≥N, curl → VPN IP, killswitch verify OK
5. TUNNEL server switch — без пароля, killswitch reinstall (endpoint IPs обновляются)
6. OFF — без пароля, туннель снят, firewall 0, curl → ISP 79.139.*
7. Profile switch — без пароля, default → popular-ai → default, sing-box check pass, Full игнорирует профиль (md5 config-full не меняется)
8. Killswitch proof — в TUNNEL stop сервис → curl 9.9.9.9 → 000 (blocked), curl 192.168.3.1 → !=000 (LAN), restart → VPN восстановлен
```

Авторитетные доказательства: `journalctl outbound/direct vs vless`, `ss -tunap`, `curl --proxy socks5h://127.0.0.1:10808` / `curl --interface tun0`, `firewall-cmd --direct --get-all-rules`. **Не** `ip route get` — врёт в policy-TUN.

Референс капитальный сьют: `~/.hermes-ssh/t_backend.sh` (S1-S16, 25 мин, S3/S4 матрицы серверов, S5 killswitch, S7 BT, S8 steam, S11 watchdog).

## Связанная документация

- `NEODON_V1_HANDOFF.md` (1669 строк, `~/Downloads/`) — полный инженерный хендофф (архитектура, контракты, gaps)
- `.planning/research/neodon-restore-research.md` — исследование SD vs host
- `.planning/phases/06-*` / `07-*` / `08-*` — CONTEXT фаз GSD
- `references/bazzite-43-freeze-operational-2026-08.md`, `bazzite-freeze-43-runbook.md` — freeze 43 (не трогать при восстановлении Neodon)
- `docs/bazzite-tailscale-setup.md`, `docs/bazzite-sddm-gaming-mode-fix.md`

---
*SD source: /run/media/m26/0000-D182/neodon-vpn (sing-box 58M, sha 8cb29c5b, 2026-08-22) · Host: bazzite 43.20260420 · Doc: 2026-08-25*
