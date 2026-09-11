# Spec 030 — Production release v0.1.0 (flow-track)

## Цель (слова владельца)
Зайти на ссылку GitHub → скачать последний релиз → запустить → вставить
ссылку провайдера → всё работает сразу (десктоп + Decky), без паролей,
без дублей, без второй настройки. Единственный ручной шаг: вставка
своей ссылки (чужую вшить нельзя — секрет).

## Архитектура (ответ на вопрос)
ОДНО приложение = бэкенд (sing-box units + scripts + state + profiles).
ДВА тонких фронта: десктоп Qt и Decky QAM-панель («шапка»). Релиз один.

## Гэпы до prod (найдены аудитом)
1. toggle.sh: `/home/m26` в 4 местах → `$HOME` (иначе чужой юзер мёртв).
2. Desktop: хардкод иконки `/home/m26/...` → expanduser.
3. examples/ + desktop/ в репо ПУСТЫ → fresh install без конфигов/ярлыка.
4. Нет config templates (live-конфиги с серверами шипить нельзя).
5. Нет converter template (live neodon-sub.py содержит СЕКРЕТ-URL).
6. sing-box не provision'ится (dep-check требует ручной установки).
7. PySide6 без fallback.
8. stage.sh собирает с живой системы, без decky/dist, версия вшита.
9. install.sh decky-копия без dist и без рестарта лоадера.

## План
- T1: $HOME + icon (repo), деплой live toggle + status-json verify.
- T2: desktop/*.desktop в репо (с хоста) + gen_templates.py → examples/.
- T3: converter template + генерация в install.sh.
- T4: install.sh: sing-box pin + PySide6 fallback + decky restart.
- T5: stage.sh rewrite (repo-source + decky build + secret scan).
- T6: сборка артефакта на хосте + скан + dry-run + verify.
- T7: GitHub Release v0.1.0 (tarball + sha256) + README quickstart.
- T8: push + отчёт + ссылка.

## Пруфы
- 53/53 + 11/11 + harness (регрессий нет).
- verify.sh VERIFY OK на хосте после правок.
- Secret scan tarball: 0 URL/UUID/IP.
- install --dry-run чистый.
