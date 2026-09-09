# Spec 024 — install.sh + verify + tarball v0.1.0-rc1 (flow-track)

## Что собрано
- `install.sh` (идемпотент, --dry-run/--uninstall/--version, deps-check,
  layout bin+repo, sudoers-template с подстановкой, verify в конце).
- `verify.sh` (exit=числу провалов): gui compile, status-json, desktop,
  sudoers (sudo-aware), units (по файлам, не шине — шина флапает),
  decky/steam опционально.
- `release/stage.sh`: tarball 50 файлов из живой системы + sha256.
- `sudoers.d/neodon-vpn.template`: только firewall --direct, tee resolv,
  loginctl linger (v0.1-owner-scope; wrapper — отдельным hardening).
- `examples/`: 3 конфига, PASS redact-check (серверы→TEST-NET, ключи→REDACTED).

## Проверено на живой Bazzite (game mode!)
- dry-run чист; два полных прогона (идемпотентность); VERIFY OK ×3 стабильно.
- Найдены и убиты по пути: флап list-unit-files, слепой [ -f ] на sudoers.d,
  дубли Steam-шорткатов (4→1 + sentinel в инсталлере).
- VPN CONNECTED всю дорогу; game mode не пострадал.

## Открыто (нужно решение владельца)
- Подпись релизов: GPG (ключ хранить/ротировать) vs cosign keyless (нужен
  GitHub Actions OIDC). Без решения — только sha256.
- Публикация: ручной `gh release create` (gh без auth здесь) + notes.
- Decky-плагин (spec 022): node отсутствует — сборка React открыта.
