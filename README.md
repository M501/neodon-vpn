# Neodon VPN

One app, two screens: **desktop** (Qt) + **game mode** (Decky QAM panel)
over a single sing-box backend. VPN never starts by itself — power button
only, default always OFF.

## ⬇️ Download & install (start here)

**Get the latest release:** https://github.com/M501/neodon-vpn/releases/latest —
download `neodon-vpn-<ver>.tar.gz`, unpack it (double-click), open the folder,
double-click **Install Neodon VPN** → type your password once → wait for
`[7/7] done`.

Then: open **Neodon VPN** (desktop) → Settings → paste the provider link →
Refresh subscription → press power. The game-mode panel appears in Decky QAM
after restarting Steam (Decky Loader itself is installed automatically when
missing).

> Developers: this page is the shop window — the code lives below, but users
> never need it. Do NOT tell users to clone the repo.

## 🗺️ Where is what

| Path | What |
|---|---|
| `install.sh` / `verify.sh` | One-click installer + post-install checker (`--dry-run`, `--uninstall`, `--no-verify`) |
| `release/` | Release pipeline: `stage.sh` (tarball), `qa-static.sh`, `qa-sandbox.sh` |
| `bin/` layout via `scripts/` | Backend: toggle/server/killswitch/dns scripts + `neodon-hostctl` |
| `tests/app/neodon-vpn.py` | Desktop Qt app (single file) + `tests/test_gui_logic.py` (pytest) |
| `decky/neodon-vpn/` | Game-mode QAM panel (thin skin over the same backend) + `test_bundle.mjs` harness |
| `profiles/` `examples/` | Routing profiles (no secrets) + sanitized config templates |
| `systemd/` `desktop/` `sudoers.d/` `flags/` | Units (shipped DISABLED), shortcuts, sudo template, country flags |
| `specs/` | Feature specs (flow-track) |
| `CHANGES.md` | Changelog: every entry has proof, no claims without logs |

## Rules of the house

- Power button only: nothing auto-connects — not at boot, not on server
  select, not on session switch. Default is always OFF.
- One backend: desktop and game mode cannot run two VPNs — same service,
  same state file, same lock, visible from both ends.
- Rule names are proper nouns and are never translated (`preset-names-verbatim`
  test enforces it).
- Subscription link is entered once (desktop) and inherited by game mode.
  It is never shipped in the package (release secret-scan enforces it).
- No completion claims without host proof: pytest on Bazzite, bundle harness,
  loader journal, `verify.sh`.
