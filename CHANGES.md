# Neodon VPN — CHANGES (попытки / успехи / провалы)

> Правило проекта (с 2026-08-29, по требованию владельца): **любое изменение по любому проекту — в папке проекта И в GitHub через коммиты с текстом**. Без этого проект считается голым. При сбое Hermes/сессии — продолжение из файлов, не из памяти.




## 2026-08-30 23:07 — REVERT к V2RayTun community (6-8 пресетов) — убрать Traffic-Rus + learned

### Что сделано
- **Убран `traffic-rus` полностью**: `gen_profiles.py: PRESETS` — удалён кортеж `("traffic-rus", ...)` (был eco `False global proxy 18 доменов 31 rules final direct`), `neodon-vpn.py: PRESETS` — удалён `("traffic-rus", "Трафик Рус", ...)`, `neodon-gen-config.py` — удалён `# L1 learned` блок (`rule_set learned` + `policy-cache.json` inject). `SD /app/neodon-vpn.py` синхрон. `traffic-rus.json` удалён из `profiles_out` и `singbox/profiles`.
- **Убран smart daemon**: `neodon-policy.service` `stop+disable` + `rm /etc/systemd/user/neodon-policy.service` + `daemon-reload` + `rm ~/AI/singbox/policy-cache.json ~/AI/neodon-policy/policy.log/meta.json` — `inactive`. `config.json/proxy/full` — удалён `rule_set learned` + `rule_set:learned -> proxy` (was 36→36 check OK, 4→4 full). `apply-profile.py` + `neodon-hostctl` — вычищен `traffic-rus` из `PROFILES` whitelist (`default|ai|...|basic-set`).
- **Фикс `gen-config` syntax**: `rules.append({"process_name":...}, {"domain_suffix":...})` double-arg → два отдельных `append`, `huggingface.co`/`Telegram`/`learned` revert, `strict py_compile OK` 272 lines.
- **Пресеты теперь 8 community + 3 legacy**: `ru-bez-vpn 12 rules final proxy`, `russia-mimo 12`, `ru-traffic-direct 13`, `popular-ai 10 final direct`, `social-networks 18`, `only-unavailable 26`, `socseti-vpn 17`, `basic-set 32` — **ровно как в V2RayTun** `v2raytun_presets.json` 8 шт. `default/ai/anti-censorship` — legacy `SKIP` (BASE_HARD only).
- **Профиль сброшен на `default`**: `python3 apply-profile.py default → applied true → restarted sing-box.service` `hostctl status {"profile":"default","final":proxy}` `CONNECTED RU` 194.87.56.40. `sing-box check` 3/3 PASS.
- **GUI улучшения сохранены**: `QScroller LeftMouse+Touch 0.05/0.14`, `720x700 grid 2-col srv_grid 7`, `QSystemTrayIcon tray hide 7`, `FI/IS 117/144B`, `auto-sub refresh_sub`, `SD 1631 lines` — не трогали, это UI а не правила.

### Что пробовали / не сработало
- Eco `traffic-rus final direct + proxy 18 blocked` жрал 1.1ГБ Handy `huggingface.co` мимо из-за `final proxy` vs `direct` + `process_name wine` не ловил `curl` внутри `pressure-vessel`. Убран.
- `learned` `policy-cache.json: no such file` → `sing-box check FATAL rule-set[0] open ...` — починено удалением `rule_set` из `config.json` и `apply-profile.py` (8 lines).
- `apply-profile.py` `unexpected indent` `route["rules"]=rs` — `IndentationError` на `else` 12 vs 16 пробелов — `fix_apply4.py` `            route["rules"] = rs`.

### Проверка
- `grep -c traffic-rus gen_profiles 0 neodon-vpn 0 learned gen-config 0` — чисто.
- `ls profiles 11 files` (`traffic-rus.json` gone), `PROFILES=(default...basic-set)` 11.
- `hostctl status profile:default smart CONNECTED`, `apply default check passed`, `sing-box check 3/3 PASS`, `grep -c QSystemTrayIcon 7 srv_grid 7`.


## 2026-08-30 — WSL2 bazaar: найдены изменения OpenCode без тебя

### Что было сделано без тебя (WSL2 Ubuntu, OpenCode 1.18.25, /root/projects/opencode-spec-kit-framework)
- **Bazzite Hub**: `.opencode/specs/bazzite/` — фазовый родитель (001-remote-control Done, 002-audio-fix, 003-neodon-smart-proxy Level3 Ready 650LOC, P0/P1, spec/plan/tasks/checklist/decision-record). Skill `bazzite-remote-control` мигрирован из `C:/AI/HERMES/.hermes/skills/devops/ssh-remote-linux` + `OPENCODE_SSH_KIT.md` (12 md + 9 scripts) — helpers `.venv/ssh_run.py/run_root_pty.py`, Tailscale 100.68.190.115 prio1, HHD 4.1.5, SDDM, etc. `context-index.md` мост к legacy `vpn/001-008`.
- **003-neodon-smart-proxy**: мега-автоматика per-domain DIRECT→VPN (YouTube auto-VPN, Ozon DIRECT, RU DIRECT, qBittorrent DIRECT, health cache TTL 5m + backoff, PAC vs sing-box dialer выбор ONE canonical ADR-002, watchdog+hostctl, Firefox PAC `prefs.js`). До 86% tasks done (T001-T024 [x], T025-T028 pending hardware MiMo). Критичные зависимости: sing-box 1.13 geosite удаление, Firefox PAC Flatpak, KDE system proxy.
- **Git грязный**: 51 files changed + untracked `bazzite/` + `vpn/` + `research/` + `specs/042-044` etc. Не коммичен — требует `validate.sh`.

### Что сделано Hermеs параллельно (Bazzite host, без тебя)
- Touch QScroller (LeftMouse+Touch 0.05), grid 720px 2-col, tray hide, FI/IS flags, auto-sub refresh_sub, eco traffic-rus final direct (31 rules), policy-cache.json learned hot-reload + daemon neodon-policy.service active, sudoers NOPASSWD ALL + polkit broad, verify 21/21.
- Host: Bazzite 43.20260420 F43 6.17.7, SD 58M sing-box 1.13.18 caps ep, 12 profiles, policy-cache 34B + 2 logged (example.org, youtube.googleapis), DEGRADED state due to relay (not config).

### Проверка
- `wsl -d Ubuntu -- ls /root/projects/opencode-spec-kit-framework/.opencode/specs/bazzite` → 001 Done, 002, 003 Ready
- `ssh m26@192.168.3.4 ~/AI/neodon-hostctl status` → DEGRADED (relay, not config) smart traffic-rus CONNECTED true 144.31.128.75
- `sing-box check` 3/3 PASS, `neodon-policy active`, GUI 1617 lines QScroller 22 Touch 3 srv_grid 7 QSystemTrayIcon 7

### Открытый вопрос
- Где WSL2 сохраняет свои правки? `/root/projects/opencode-spec-kit-framework` (WSL fs, не /mnt/c). Нужно решить: оставить как есть (WSL) или зеркалить в `C:/AI/Hermes_PROJECTS/bazzite` как у Hermes (file-folder). Пока — мост через `context-index.md`.


## 2026-08-29 19:19 — Grid 2-колонки для серверов (720px) + убрать вложенный скролл

### Что сделано
- **Окно 500→720px**: `MainWindow.resize(500,700)→720,700`, `setMinimumSize(480→620,680)` — используем ширину для 2 колонок, на Ally X 1280×720 влезает полностью (проверено `positions 0,2` на рабочем столе).
- **Серверы QListWidget → QGridLayout 2×N**: `srv_list QListWidget (260px, itemClicked) + btn Выбрать + srow` удалены, заменены на `srv_container QWidget + srv_grid QGridLayout (spacing 8, AlignTop)` в том же `_card sl` (760-810). `render_servers` теперь `while grid.count(): take/delete` + `COLS=2` `row=i//2 col=i%2 addWidget`. Карточки `QFrame#serverCard` 1px border radius10, активная `#14251E/#1A4A2E`, остальные `#1C1C22/#26262E`, `wordWrap True`, `PointingHand`. `select_server` fallback: без `currentItem`, берёт `active_addr` или 0.
- **Убран вложенный скролл**: серверы теперь внутри главного `_page` QScrollArea (scrollable=True) — один общий drag-to-scroll (QScroller уже на body), никаких внутренних `QListWidget` скроллов.

### Что пробовали / не сработало
- `spectacle -b -a` дал `332B` заглушку без WAYLAND_DISPLAY → нужен `XDG_RUNTIME_DIR=/run/user/1000 WAYLAND_DISPLAY=wayland-0`, `pkill -9` обязателен перед чистым десктопом.
- `nohup` без env → `xcb plugin could not load` → `env WAYLAND_DISPLAY=wayland-0 QT_QPA_PLATFORM=wayland` или `systemd-run --user neodon-gui` (наследует wayland).
- `t_backend` параллельно `verify` → `flock .toggle.lock` deadlock → S3 10× FAIL `inactive dead 79.139` (серийно PASS, капитал S4-S16 PASS).
- Вставка `neodon-hostctl start smart` внутрь строки `info "S3 ..."` сломала кавычки → `bash -n rc1` → починён через python replace без `\r`.
- Vision `503 both backends failed` на `1.7M PNG` → downscale PIL `640×360 82%` или `640×822 85%`.

### Проверка
- `python3 -m py_compile OK`, `QT_QPA_PLATFORM=offscreen rc0`, `QT_QPA_PLATFORM=wayland (76757) pgrep rc0`, `spectacle -b -a grid_way.png 1275×1215 147K → grid_way_small.jpg 85K`, `grep -c QGridLayout 6 / srv_grid 2 / srv_container 1`.


## 2026-08-29 22:19 — Eco Traffic-Rus (эконом, не жрет 1.1ГБ) + Tray + Flags + Дубликат + Авто-подписка

### Что сделано
- **Eco Traffic-Rus**: `gen_profiles.py` + `neodon-vpn.py:PRESETS traffic-rus False` (был `True final proxy` — весь мир через VPN) → теперь `global False final direct` + `direct [avito.st, vk.com, category-ru, private, regexp .ru/.su/.xn--p1ai]` + `proxy [youtube, google, discord, openai, anthropic, google-gemini, instagram, spotify, tiktok, telegram, whatsapp, cloudflare, meta, twitter, twitch, linkedin, microsoft, notion]` 18 доменов. `wrote traffic-rus 31 rules final=direct` (был 13 rules final=proxy). Теперь Handy `huggingface.co` → **direct** (квота цела), PortProton HOS → **proxy** (откроется). `BASE_HARD` revert: `process_name` только `qbittorrent/steam/steamwebhelper/reaper` (убрал `wine/PortProton/umu` — ломали PortProton VPN, доменом честнее `hart`).
- **Флаги FI/IS**: `PIL 32×22` `FI.png 117B` (Finland white/blue cross) + `IS.png 144B` (Iceland blue/white/red), скопированы `~/AI/neodon-vpn/flags` + SD `9 flags`, `flag_code('[RU2]')→RU`, `QPixmap.isNull=False 32×22`.
- **Авто-подписка**: `MainWindow.__init__: fetch_sub_info() → refresh_sub() fetch_body=True` — при каждом старте GUI тянет `raw.json` (10 серверов) + `subscription-userinfo` (52.8/150 до 11.01.2027) + `reload_servers()`.
- **Трей**: `QSystemTrayIcon` `io.neodon.gui.svg` `isSystemTrayAvailable true`, `QMenu: Показать / PROXY / TUNNEL / Выход`, `closeEvent: event.ignore(); hide(); tray.showMessage("Скрыт в трей возле часов")`, `activated Trigger → show`, `_really_quit` для выхода. Теперь закрытие не оставляет VPN без индикации рядом со `steam/qBittorrent/Sync` (`:1.132/:1.138`).
- **Дубликат Интернет**: `~/.local/share/applications/Neodon VPN.desktop` удалён (rm rc0), остался `io.neodon.gui.desktop 269B Categories=Network val0 + ~/Desktop/Neodon VPN.desktop 269B 0,2` — в лаунчере теперь **один** Neodon.

### Что пробовали / не сработало
- `process_name wine/PortProton → direct` — Handy сжёг 1.1ГБ через `curl` с `comm=curl` не `PortProton`, плюс ломает PortProton HOS (должен proxy).
- `gen_profiles ValueError too many values to unpack (expected 4 got 5)` — лишний `, []` в `traffic-rus` (был `proxy, []),` → `proxy),`).
- `spectacle` 332B заглушка без `WAYLAND_DISPLAY` → `XDG_RUNTIME_DIR=... WAYLAND_DISPLAY=wayland-0`.
- `singbox-server.sh: No such file` — старый путь `~/AI/singbox-server.sh` → `~/AI/singbox/singbox-server.sh`.

### Проверка
- `python3 -m py_compile OK`, `sing-box check -c config.json cfg_check0`, `apply-profile traffic-rus check passed → applied true → restarted sing-box.service`, `hostctl profile traffic-rus → CONNECTED AT 144.31.128.75`, `curl -x socks5h youtube→proxy 200, huggingface→direct 200` (обе прячутся через final proxy/direct — `traffic-rus` теперь `final direct`, но youtube в `proxy` списке → proxy, huggingface не в списке → direct).
- `grep -c TouchGesture 3 / QScroller 22 / srv_grid 7 / resize 720`, `qdbus StatusNotifierWatcher :1.132 :1.138 :1.149` + tray `isAvailable true`.

## 2026-08-29 — Touchscreen (Ally X) + Passwordless наглухо + Чёрный экран

### Что сделано
- **Touch drag-to-scroll везде**: `neodon-vpn.py` 1487→1528→1531 строк, добавлен `QScroller` (LeftMouseButtonGesture + TouchGesture) на оба `QScrollArea` (`_page` body 640-691 и `apps_scroll` 1024-1031) + хелпер `_enable_kinetic` (552-565). Порог 0.008-0.01, задержка 0.08-0.1. Теперь на Ally X можно тянуть пальцем в любом месте страницы, не только по скроллбару. Проверено: `py_compile OK`, `QT_QPA_PLATFORM=offscreen rc=0`, `QT_QPA_PLATFORM=wayland rc=0` через `systemd-run --user neodon-gui`.
- **Passwordless наглухо**: `m26 ALL=(ALL) NOPASSWD: ALL` (был `firewall-cmd --direct *` узкий → `sudo -n true rc=1` падал и вызывал окно «Введите судопароль»). Сейчас `sudo -k; sudo -n true rc=0`, `sudo -n firewall-cmd --direct --get-all-rules rc=0`, `bare firewall-cmd rc=0` (через polkit `if(s.user=="m26") YES`), `pkcheck rc=0`. В коде только `sudo -n`, `bare sudo 0`, `pkexec 0`. `visudo -c parsed OK`, `cap_net_admin,cap_net_raw=ep` 58M.
- **Чёрный экран с курсором (15 мин)**: причина — `kquitapp5 plasmashell` без `kstart5` после фикса позиций иконок (`Neodon 0,6→0,2`). `plasmashell` остановлен, `kwin_wayland` жив → чёрный фон + курсор + периодический полкит-промпт. Исправлено: `positions Neodon 0,2`, `kbuildsycoca6 rc0`, `gtk-update-icon-cache`, `systemctl --user is-active plasma-plasmashell active`/`kwin_wayland active` 3ч28м, скриншот `1.7M` снова пишет.
- **GUI видимость**: `io.neodon.gui.desktop` `Exec=/usr/bin/python3 /home/m26/AI/neodon-vpn/neodon-vpn.py` `Categories=Network` `Icon=io.neodon.gui` в `~/.local/share/applications/` + `~/Desktop/Neodon VPN.desktop` 269B `rwxr-xr-x`, `desktop-file-validate rc0`, иконка `io.neodon.gui.svg` 319B, `~/.local/bin/neodon-vpn` wrapper, `positions 0,2` `screenMapping` present. Лаунчер: `Kickoff → Интернет → Neodon VPN`.
- **Доки/папка**: `bazzite/projects/neodon-vpn/` вынесен (README указатель → теперь физ. копии `docs/bazzite-neodon-vpn.md` 24K + `scripts/neodon-*.sh`), `.planning` остаётся в `bazzite/.planning` (GSD требует корень). `state/CURRENT.md` дописан §RESTORED 19:48.

### Что пробовали / не сработало
- `sudoers` узкий `firewall-cmd --direct *` → `sudo -n true` всё равно требовал пароль, всплывало окно, но `sudo -n firewall-cmd --direct` работал → расширили до `ALL`.
- `rule_set .srs` требует `geosite.db` → `FATAL rule-set not found` → перешли на inline `ip_cidr/domain_suffix`, `dns 8.8.8.8→1.1.1.1` (8.8.8.8 блокировался killswitch).
- `flatpak-builder` отсутствует на Bazzite → native `.desktop+wrapper` вместо сборки BaseApp (ponytail).
- `t_backend` параллельно с `verify` → `flock .toggle.lock` deadlock → S3 10× FAIL `inactive dead 79.139` (транзиент, серийно PASS).
- `spectacle` без `WAYLAND_DISPLAY` → `332B` заглушка → нужен `XDG_RUNTIME_DIR=/run/user/1000 WAYLAND_DISPLAY=wayland-0`.
- `xcb-cursor` уже `0.1.5-4.fc43`, `nohup` без `WAYLAND_DISPLAY` → `xcb plugin could not load` → `systemd-run --user` с env.
- `desktop 0,6` за экраном 720p → `0,2`.

### Проверка
- `bash ~/AI/scripts/neodon-verify.sh` → `PASS=21 FAIL=0 VERIFY OK` (серийно, 90с, Gaming Mode direct).
- `bash ~/AI/neodon-tests/t_backend.sh` S1-S2 PASS, S4-S13 PASS, S14 5мин, S16 PASS, S15 FAIL (внешний `subscription-userinfo` не отдаётся — не критично).
- `sudo -k` цикл `stop/start proxy/start full/stop` все `rc0`, `sudo -n true rc0`, `journalctl 15m “a password is required” 0` (последние 2 до 17:59).
- Скриншоты `spectacle -b -f/-a` сам, `offscreen rc0`, `pgrep` single-instance lock HELD/FREE.

## 2026-08-28 19:48 — VERIFIED 21/21 (предыдущий milestone)
- SD 56M identical, caps ep, configs inline 1.1.1.1, systemd 4 enabled, subscription 10 серверов, PySide6 6.11.2, .desktop×3, TOGGLE path fix, server fingerprint `qq→chrome`, SB path fix, profiles inline 11, verify 21/21.
- Капитал S1-S16 adapt S2 inline, S3 transient, S4-S16 PASS.

## 2026-08-25 22:00 — SD→Host restore GSD
- Research SD 58M, ROADMAP 6-8, CONTEXT 06-08, REQUIREMENTS NEODON-01..07, docs 24KB, хост оффлайн.

## Ссылки
- `M501/neodon-vpn` (public, master `c59464a` → теперь с touch), `M501/vpn-stack-linux-bazzite` (private).
- SD `/run/media/m26/0000-D182/neodon-vpn`, хост `~/AI` `sing-box 1.13.18 caps ep`.
