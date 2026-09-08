# Spec 015 — дубли снесены везде (flow-track, converge)

## Команда
Удалить дубли (russia-mimo, ru-traffic-direct); v2RayTun на Windows НЕ трогать.

## Что сделано (вслед за параллельной сессией, convergence без конфликтов)
- GUI уже был 7 пресетов у них; мой diff — ровно удаление (доказано diff).
- Мной: hostctl + apply-profile whitelists, profiles/*.json ×2, 3 bak-папки,
  12 patcher-бэкапов, stale `~/AI/gen_full_profiles.py` обновлён из репо.
- apply-profile.py принят в репо как truth.
- v2RayTun Windows: НЕ ТРОНУТ (процесс жив, пресеты целы) — запрет владельца.

## Verify
- reject russia-mimo; ru-bez-vpn --check passed; AUDIT-OK (absence-check зелёный).
- 35/35 pytest; live md5 == project; рестарт; CONNECTED.
