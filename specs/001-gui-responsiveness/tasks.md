# Tasks 001 — порядок: тесты → код → зелёные → live (flow-track)

- [x] T1. Каркас: `tests/test_gui_logic.py` — 3 passed on HOST (pytest 9.1.1 + pytest-qt 4.5.0 + PySide6 6.11.2, offscreen, 0.07с). Первично хост `~/AI/neodon-tests/`, Windows-венв вторичен. Чистые функции sub-парса ок → пустой дисплей подписки НЕ парс-баг (сеть/аккаунт).
- [x] T1b. Расширить: set_state переходы, single-flight, QScroller-хелпер (qtbot, offscreen) — красный старт перед кодом.
- [x] T2. P0 poll: `_poll_busy` single-flight + пропуск с счётчиком, интервал 4→8с, статус fast-path (лёгкий JSON сейчас; тяжёлый exit_ip/latency — отдельный воркер 60с). Убрать `fetch_exit_ip` (дубль).
- [x] T3. P0 set_state: единый `set_state(s)` — CONNECTED стартует таймер-эпоху GUI, OFF/STOPPING/FAILED стопают+обнуляют; трей-иконка off/on/wait + тултип `состояние · сервер`; кнопки дизейбл при TRANSITIONING.
- [x] T4. P0 select: разбить SelectWorker на фазы (server 10с → toggle 12с) с прогрессом в pill/statusBar; rollback-текст причины.
- [x] T5. P1 touch: один `_enable_kinetic` (Touch-only, Delay 0.06, Distance 0.012, OvershootOff, ScrollPerPixel), удалить дубли и мёртвый блок; тап не глотается.
- [x] T6. P1 sub: кэш последнего валидного + причина N/A (сеть/парс/total) + фон-обновление 30 мин + скелетон.
- [x] T7. P1 гигиена: чистка `_workers` по done; quit без последовательных wait (bounded total).
- [ ] T8. Верификация: pytest зелёные → py_compile → копия на хост (SFTP, бэкап `.bak-gui001`) → offscreen smoke → live: `ps` без висяков, свитч <3с, GSR-запись тапа/флика по требованию → `audit_parity` регресс → CHANGES + push + отчёт DONE/CAVEATS/BLOCKED.
- [ ] T9 (отдельно, не в этом спеке): смена дефолта SMART→PROXY по замерам; полный verify.sh в окно простоя; motion-QA стенд (GSR+portal-restore).
