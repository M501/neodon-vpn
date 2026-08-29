# Neodon VPN — CHANGES (попытки / успехи / провалы)

> Правило проекта (с 2026-08-29, по требованию владельца): **любое изменение по любому проекту — в папке проекта И в GitHub через коммиты с текстом**. Без этого проект считается голым. При сбое Hermes/сессии — продолжение из файлов, не из памяти.

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
