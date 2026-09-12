# Neodon VPN

One app, two screens: desktop (Qt) + game mode (Decky QAM) over a single
sing-box backend. VPN never starts by itself — only the power button.

## Install (no terminal needed)

1. Download `neodon-vpn-<ver>.tar.gz` from
   [Releases](https://github.com/M501/neodon-vpn/releases) and unpack it
   (double-click in the file manager).
2. Open the unpacked folder, double-click **Install Neodon VPN**,
   choose Run/Execute. Type your password once if asked.
3. Wait for `[7/7] done`. Open **Neodon VPN** (desktop) → Settings →
   paste the provider link → Refresh subscription → press power.

Game-mode panel appears in Decky QAM after restarting Steam
(Decky Loader itself is installed automatically when missing).

## Rules of the house

- Power button only: nothing auto-connects — not at boot, not on server
  select, not on session switch. Default is always OFF.
- One backend: desktop and game mode cannot run two VPNs — same service,
  same state, visible from both ends.
- Subscription link is entered once (desktop) and inherited by game mode.
  It is never shipped in the package.
