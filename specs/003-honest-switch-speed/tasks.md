# Tasks 003 — honest-switch-speed (flow-track, закрыто 2026-09-07)

- [x] T1. Замер: toggle 0.8с, опросы 2.6/4.6с, фазы 0.75с, listen 20мс (measure_*.sh).
- [x] T2. `patch_status_fast.py`: `-m` 3→2/8→3, latency timeout 2→1, маркер до CONNECTED/OFF, switching-сообщения.
- [x] T3. `patch_status_gated.py`: гейты tun/10808 (неготовые опросы ~0.5с).
- [x] T4. `patch_status_marker.py`: deadlock-фикс (кандидат → оверрайд маркера).
- [x] T5. GUI: `_fast_poll_wanted` + arm в toggle + notify-on-CONNECTED (Popen).
- [x] T6. 17/17 pytest хост → деплой → GUI рестарт (1 инстанс, поллит, без ошибок).
- [x] T7. Live круг: proxy 3с, smart 2с (было ~10с). CHANGES + push + отчёт.
