# neodon-vpn — проект внутри bazzite

Подпроект VPN (v2RayTun-клон, sing-box 1.13.18) внутри `bazzite/` чтобы не мешать `framegen`/`freeze` контексту.

## Где что реально лежит (пока без физического переноса — указатели)

- **Дока:** [`../../docs/bazzite-neodon-vpn.md`](../../docs/bazzite-neodon-vpn.md) — 24KB, SD→Host, PROXY vs TUNNEL, presets, passwordless
- **Research:** [`../../.planning/research/neodon-restore-research.md`](../../.planning/research/neodon-restore-research.md)
- **GSD фазы:** [`../../.planning/phases/06-neodon-restore-sd-to-host/`](../../.planning/phases/06-neodon-restore-sd-to-host/) + `07-…` + `08-…` + `ROADMAP.md` 06-08 + `REQUIREMENTS.md` NEODON-01..07
- **Скрипты:** [`../../scripts/neodon-restore.sh`](../../scripts/neodon-restore.sh) / `neodon-passwordless.sh` / `neodon-verify.sh` → копии уедут в `~/AI/scripts/` на базе
- **Хендофф:** `C:/Users/M25/Downloads/NEODON_V1_HANDOFF.md` (1669 строк, frozen 2026-08-18)
- **Хост:** `~/AI` (sing-box, toggle, hostctl, singbox/*.json), `~/.config/systemd/user/` (3 юнита + boot)

## Структура когда проектов станет 2+

```
bazzite/projects/
├── neodon-vpn/   ← ты тут (этот README = индекс)
└── framegen/     ← следующий проект — тогда физически перенесём docs/scripts сюда
```

Пока второй проект не активен — файлы остаются в `bazzite/docs|scripts|.planning` чтобы не ломать GSD (`.planning` живёт только в корне). Перенос — одна команда `git mv` когда понадобится.


## Фактически сейчас (2026-08-28 19:48, VERIFY 21/21 PASS)

- **Копии в проекте:** `docs/bazzite-neodon-vpn.md` + `scripts/neodon-*.sh` — физические копии (ponytail: .planning остаётся в корне `bazzite/.planning` — GSD требует корень, туда не переносим).
- **Хост:** `~/AI` восстановлен, `sing-box 1.13.18 caps ep`, `config.json/proxy/full` inline `1.1.1.1` без rule_set, `systemd --user` 4 юнита enabled, `PySide6 6.11.2`, `.desktop`×3 в `~/.local/share/applications/` + `~/Desktop`, `neodon-vpn` wrapper в `~/.local/bin`, `kbuildsycoca6` перезапущен.
- **Доказательство:** `bash ~/AI/scripts/neodon-verify.sh` → `PASS=21 FAIL=0 VERIFY OK` (Gaming Mode не мешал, SD `/run/media/m26/0000-D182` 56M identical).


> **Правило (с 2026-08-29):** каждое изменение — в папке `bazzite/projects/neodon-vpn/` И в GitHub `M501/neodon-vpn` коммитом с текстом (что делал/пробовал/сработало/нет). Без этого проект голый. Восстановление из файлов, не из памяти Hermes.

## Запуск (на базе, SD вставлена)

```bash
bash ~/AI/scripts/neodon-restore.sh      # Phase 6: SD→Host + sing-box 58M + caps
bash ~/AI/scripts/neodon-passwordless.sh # Phase 7: sudoers/polkit + PROXY 10808 + TUNNEL tun0/killswitch
bash ~/AI/scripts/neodon-verify.sh       # Phase 8: 8 тестов без пароля — критерий "ни одного sudo пароля"
```
