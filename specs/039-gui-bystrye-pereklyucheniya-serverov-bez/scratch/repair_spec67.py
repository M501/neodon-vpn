"""Repair spec.md (sections 6/7 were swapped by an earlier reorder) and normalise newlines."""
import os
import re

os.chdir(os.path.dirname(os.path.abspath(__file__)) + "/..")

AUDIT = """## 6. RISKS & DEPENDENCIES

| Type | Item | Impact | Mitigation |
|------|------|--------|------------|
| Dependency | Clash API `127.0.0.1:9090` | при OFF недоступен | `curl -m 1`; отсутствие API = нет метки живой ноды |
| Dependency | `selected-server.json` | нет файла | пустой выбор = нет подсветки |
| Risk | Эвристика второго тапа может признать тапом лишний жест | Средний | правило ограничено окном 0.6 с и требует неподвижного скролла; отдельный тест «overscroll при неизменном скролле» |
| Risk | Qt-поведение DblClick зависит от системного интервала двойного клика | Низкий | окно 0.6 с шире типового интервала (обычно 0.4 с) |
| Risk | Живой процесс держит старый код | Средний | рестарт GUI + пиксельная проба до/после |

## 7. AUDIT FINDINGS (три независимых read-only ревью: GUI, control-plane, Decky)

| # | Severity | Где | Суть | Решение | Проверка |
|---|----------|-----|------|---------|----------|
| A1 | major | `neodon-vpn.py` `save_sub_url` | URL из Settings вставлялся в `.py`-файл через `%`-форматирование без экранирования: кавычка или перевод строки портят (или инжектят код в) конвертер подписки | ИСПРАВЛЕНО: отказ на кавычки, бэкслеши и переводы строк | `py_compile` + отказ в UI с текстом ошибки |
| A2 | major | `neodon-vpn.py` `refresh_sub` + `/tmp/neodon_*` | Не было защиты от повторного запуска, временные файлы фиксированные: два refresh (кнопка, таймер 30 мин, а также Decky) могли переписать `raw.json` чужим недописанным телом (пустой список серверов) | ИСПРАВЛЕНО: флаг `_sub_busy` (снимается в успехе и в ошибке) + имена с PID | второй запуск получает «Refresh already running…»; `raw.json` не меняется |
| A3 | major | `neodon-vpn.py` `PingWorker` | Результаты пинга прошлой сетки писались в индекс новой (после `reload_servers`): мс вставала не к тому серверу; второй Ping мог идти параллельно | ИСПРАВЛЕНО: поколение списка `_srv_gen` + флаг `_ping_busy` | ветка отбрасывает чужое поколение; `py_compile` |
| A4 | minor | `neodon-vpn.py` `_status_loaded` | `connected` брался из «сырого» состояния, а `state` — из дебаунсенного: один мигающий полл переворачивал смысл нажатия питания | ИСПРАВЛЕНО: `connected = (state == "CONNECTED")` | grep: `connected` используется только в `on_power` |
| A5 | minor | `neodon-vpn.py` `__init__` | `current_mode()` вызывался дважды (два медленных обращения к бэкенду на старте) | ИСПРАВЛЕНО: одно чтение | запуск GUI, `py_compile` |
| A6 | minor | `neodon-vpn.py` `ENV` | `XDG_RUNTIME_DIR` жёстко `/run/user/1000` | ИСПРАВЛЕНО: из окружения либо по `os.getuid()` | grep: единственное вхождение |
| A7 | minor | `neodon-vpn.py` Settings/Apps | Мёртвый UI: поле «DNS» и кнопка «Apply» на Apps ничего не делают; мёртвые методы `select_server` и `status_meta_ip`; дублирующий блок импортов и 6 неиспользуемых имён | ИСПРАВЛЕНО: удалено | все страницы открываются после чистки (снимки `pg_*.png`), GUI жив |
| A8 | major | репо: корневые `singbox-toggle.sh`, `singbox-server.sh`, `killswitch.sh` | Дубли не попадают в релиз (`install.sh` и `stage.sh` берут `scripts/`), и `killswitch.sh` уже разошёлся: старая широкая DNS-дыра в prio 4 | ИСПРАВЛЕНО: удалены | `stage.sh` явно требует `scripts/$f`; ссылок на корневые пути в репо нет |
| A9 | major | `scripts/singbox-toggle.sh` (`off`) | Разблокировка фаервола была условной, и при неудаче всё равно печаталось «VPN OFF — internet via ISP», хотя fail-closed REJECT оставался | ИСПРАВЛЕНО: разблокировка повторяется безусловно, сообщение проверяется фактом | живой прогон smart→off: 0 правил prio 20, exit-IP = провайдер, юниты inactive |
| A10 | major (отложено) | Decky-панель | Панель не знает режим `proxy` (показывает как smart и переключает в smart); у смены режима нет quiet-окна; ошибки `get_status` маскируются под обычный полл; поллы могут накладываться | ОТЛОЖЕНО: правка фронтенда требует сборки бандла и рестарта Steam, жалоба владельца была про десктоп | — |
| A11 | major (отложено) | `neodon-vpn.py` `_list_apps` | `flatpak list` (до 10 с) выполняется в GUI-потоке при открытии страницы Apps | ОТЛОЖЕНО: нужен вынос в воркер; страница редкая, риск правки в этой волне выше пользы | — |
| A12 | minor (отложено) | `neodon-vpn.py` `ENV` | В дочерние процессы уходит всё окружение сессии (возможные секреты) | ОТЛОЖЕНО: минимальный env ломает `systemctl --user` и dbus в скриптах — нужен отдельный проверенный проход | — |
| A13 | minor (отложено) | `scripts/singbox-toggle.sh` `locked` | Проба фаервола только для `full|off`: при рассинхроне `.mode=smart` + REJECT состояние LOCKED не видно | ОТЛОЖЕНО: безусловная проба = `sudo` на каждом полле статуса (8 с) | — |
| A14 | minor (отложено) | `neodon-sub.py`, `.mode`/`.desired`, sudoers-шаблон | Жёсткие `/home/m26` и неатомарная запись `raw.json`; heal пишет `.mode=off`, не трогая `.desired`; в шаблоне sudoers нет `ip rule/route/link` | ОТЛОЖЕНО: на этом хосте не проявляется | — |
"""

doc = open("spec.md", encoding="utf-8", newline="").read().replace("\r\n", "\n")
start = doc.index("## 6. ")
end = doc.index("## L2: NON-FUNCTIONAL REQUIREMENTS")
doc = doc[:start] + AUDIT + "\n" + doc[end:]
open("spec.md", "w", encoding="utf-8", newline="").write(doc)
print("spec.md sections 6/7 restored")

for name in ("spec.md", "plan.md", "tasks.md", "checklist.md", "implementation-summary.md"):
    text = open(name, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    open(name, "w", encoding="utf-8", newline="").write(text)
    print("LF ok:", name)
