# Spec 020 — вердикт консилиума: упаковка + Game Mode (paper-track)

## Решения (3 места единогласно, противоречий нет)
1. Упаковка: GitHub Releases + `install.sh` сейчас; COPR/rpm-ostree позже;
   Flatpak/Distrobox/Gear Lever/демоны/silent-update — НЕ строить.
2. Game Mode: тонкий Decky-плагин поверх bash-backend (QAM: статус/режим/
   сервер/вкл-выкл/переподключить, крупно, геймпад); конфиг только в Desktop;
   Qt-шорткат — только запасной путь без доработок.
3. Ребут: VPN-автостарт оставить (юнит+linger), GUI в автостарт НЕ добавлять
   (battery rule; статус виден в Decky). Мёртвый чекбокс СНЕСТИ (сделано).
4. Обновления: явная кнопка + бейдж версии, install по нажатию; никаких
   фоновых чекеров/таймеров (проверено: их нет).
5. Безопасность шиппа: sudoers-wrapper с allowlist (не голый firewall-cmd),
   SHA256+GPG до запуска, `--uninstall`, redox red lines (no curl|sudo bash,
   no NOPASSWD ALL, no shell=True, no permanent без отката).

## Проверено на железе
- Decky стоит (~/homebrew + Decky-Framegen), сервис спит до Game Mode — норма.
- sudo-база: NOPASSWD ALL (конфиг владельца, для шиппа — wrapper).
- Чекбокс снесён + тест; 45/45; деплой + рестарт.

## Следующие шаги (по порядку)
1. `ujust setup-decky` verify + TunnelDeck из стора → валидация пути.
2. install.sh + tarball + SHA256/GPG → прогнать на живой Bazzite.
3. neodon-decky плагин (root-флаг, QAM-панель, subprocess-обёртки).
