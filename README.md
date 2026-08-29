# Neodon VPN

VPN client for Linux/Bazzite, inspired by v2RayTun.

## Features
- PySide6 GUI (8 community presets)
- sing-box 1.13.18 (TUN + PROXY modes)
- Killswitch (L2 fail-closed)
- Watchdog with failover
- Flatpak build
- CLI: neodon-hostctl status/start/stop/server N

## Installation on Bazzite

### 1. Install sing-box
wget https://github.com/SagerNet/sing-box/releases/download/v1.13.18/sing-box-1.13.18-linux-amd64.tar.gz
tar xzf sing-box-1.13.18-linux-amd64.tar.gz
sudo cp sing-box-1.13.18-linux-amd64/sing-box /usr/local/bin/

### 2. Clone repository
git clone https://github.com/YOUR_USERNAME/neodon-vpn.git ~/AI/neodon-vpn
cd ~/AI/neodon-vpn
chmod +x *.sh neodon-hostctl

### 3. Setup subscription
python3 ~/AI/neodon-sub/neodon-sub.py

### 4. Flatpak (GUI)
cd ~/AI/neodon-flatpak
flatpak run org.flatpak.Builder --user --force-clean --repo=repo builddir io.neodon.gui.json
flatpak install --user repo io.neodon.gui

## Usage

### CLI
~/AI/neodon-hostctl status
~/AI/neodon-hostctl start smart
~/AI/neodon-hostctl stop
~/AI/neodon-hostctl server 1  # NL

### GUI
flatpak run io.neodon.gui

## Requirements
- Bazzite Linux (or other Fedora-based)
- Python 3.11+
- PySide6
- sing-box 1.13.18
- KDE Plasma (Wayland)

## License
MIT

## Documentation
- `docs/bazzite-neodon-vpn.md` — full restore guide (PROXY vs TUNNEL, presets, passwordless, touchscreen 2026-08-29)
- `CHANGES.md` — what was tried / failed / succeeded (2026-08-29 touch + passwordless nagluho)
- `state/CURRENT.md` in bazzite project — host state 19:48 VERIFIED 21/21
