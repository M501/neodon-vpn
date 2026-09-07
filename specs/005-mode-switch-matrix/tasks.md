# Tasks 005 — mode-switch-matrix (flow-track, закрыто 2026-09-08)

- [x] T1. Флип подсветки: guard `_op_in_progress` + тест rehighlight.
- [x] T2. Замер full: toggle 14с, ks-install 9.4с из них.
- [x] T3. REJECT-only remove + LOCKED-по-REJECT (patch_ks_rejectonly, patch_toggle_locked).
- [x] T4. fullopt: маркер→-m 5, warmup, tun-poll, цикл 0.2с (patch_status_full).
- [x] T5. Deadlock маркера (patch_status_marker) — вечный TRANSITIONING.
- [x] T6. DNS-сука 53-only + миграция + prune stale (patch_ks_dnsnarrow).
- [x] T7. Leak A/B: full rc=7, smart/off открыты; ip rule чистые.
- [x] T8. 22/22 хост → redeploy → матрица 4с/4с/1с → CHANGES + push.
