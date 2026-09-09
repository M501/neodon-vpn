# Spec 025 — Decky-плагин Neodon VPN (flow-track)

## Что построено
- `decky/neodon-vpn/`: plugin.json (без root-флага — backend user-level),
  package.json, rollup.config.js, tsconfig.json, main.py, src/index.tsx,
  test_backend.py.
- Backend: только allowlist-argv (up/down/mode/server), чтения JSON,
  env-scrub LD_LIBRARY_PATH, таймауты. 6/6 headless-тестов на хосте.
- QAM-панель: статус+exit, toggle, PROXY/TUNNEL dropdown, сервер dropdown,
  Переподключить, квота. Poll 5с.

## По пути через грабли
- brew node (v26.8.1) — штатно.
- rollup musl-пин снят (glibc-хост), ServerAPI→any (@decky/ui не экспортит).
- Чистая сборка dist/index.js 7854 bytes.
- `~/homebrew/plugins` root-owned → sudo mkdir + chown (как у Framegen).

## Verify
- Loader: found → Loaded v0.1.0 → backend up, без трейсбеков.
- Осталось глазам: QAM → Neodon VPN → вкл/режим/сервер.
