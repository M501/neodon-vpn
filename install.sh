#!/usr/bin/env bash
# Neodon VPN — one-click installer (GitHub Release tarball entry point).
# Idempotent: re-running repairs instead of duplicating. Never runs the VPN.
# Usage: bash install.sh [--dry-run] [--uninstall] [--help] [--version]
set -euo pipefail

VERSION="0.1.0-rc1"
SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# tarball layout (bin/) or repo layout (scripts/) — both work
BIN="$SRC/bin"; [ -d "$BIN" ] || BIN="$SRC/scripts"
GUI_SRC="$SRC/bin/neodon-vpn.py"; [ -f "$GUI_SRC" ] || GUI_SRC="$SRC/tests/app/neodon-vpn.py"
DRY=0
DO_UNINSTALL=0

log()  { echo "neodon-install: $*"; }
dry()  { if [ "$DRY" = 1 ]; then echo "  [dry-run] $*"; return 0; fi; return 1; }

for a in "$@"; do
  case "$a" in
    --dry-run) DRY=1 ;;
    --uninstall) DO_UNINSTALL=1 ;;
    --version) echo "$VERSION"; exit 0 ;;
    --help|-h)
      echo "Usage: bash install.sh [--dry-run] [--uninstall] [--help] [--version]"; exit 0 ;;
    *) echo "unknown arg: $a" >&2; exit 2 ;;
  esac
done

need() { command -v "$1" >/dev/null 2>&1 || { echo "MISSING dep: $1" >&2; return 1; }; }

do_uninstall() {
  log "uninstalling (config/secrets kept, use --purge manually if needed)..."
  dry "systemctl --user disable --now sing-box.service sing-box-full.service sing-box-proxy.service" \
    || systemctl --user disable --now sing-box.service sing-box-full.service sing-box-proxy.service 2>/dev/null || true
  dry "rm -rf ~/.local/bin/neodon-* ~/homebrew/plugins/neodon-vpn" \
    || { rm -f ~/.local/bin/neodon-hostctl ~/.local/bin/neodon-vpn.py; rm -rf ~/homebrew/plugins/neodon-vpn; }
  dry "rm -f ~/.local/share/applications/io.neodon.gui.desktop" \
    || rm -f ~/.local/share/applications/io.neodon.gui.desktop
  if [ -f /etc/sudoers.d/neodon-vpn ]; then
    log "sudoers file left in place (remove manually): /etc/sudoers.d/neodon-vpn"
  fi
  log "uninstall complete."
}

if [ "$DO_UNINSTALL" = 1 ]; then do_uninstall; exit 0; fi

log "Neodon VPN $VERSION (dry-run=$DRY)"
MISSING=0
for dep in python3 sing-box firewall-cmd systemctl; do
  need "$dep" || MISSING=1
done
python3 -c "import PySide6" 2>/dev/null || { echo "MISSING dep: python3-PySide6" >&2; MISSING=1; }
if [ "$MISSING" = 1 ]; then
  echo "Install missing deps first (Bazzite: rpm-ostree / flatpak, manual step)." >&2
  exit 2
fi
log "deps OK"

# 1. files: backend + GUI into ~/AI (live layout), bins into ~/.local/bin
dry "mkdir -p ~/AI/singbox ~/AI/singbox/profiles ~/AI/neodon-vpn/icons ~/.local/bin ~/.local/share/applications" \
  || mkdir -p ~/AI/singbox ~/AI/singbox/profiles ~/AI/neodon-vpn/icons ~/.local/bin ~/.local/share/applications
for f in singbox-toggle.sh singbox-server.sh killswitch.sh dns-fix.sh apply-profile.py; do
  [ -f "$BIN/$f" ] || { echo "package broken: $f missing in $BIN" >&2; exit 3; }
  dry "install -Dm755 $f ~/AI/singbox/$f" || install -Dm755 "$BIN/$f" "$HOME/AI/singbox/$f"
done
[ -f "$BIN/neodon-hostctl" ] || { echo "package broken: neodon-hostctl missing" >&2; exit 3; }
dry "install -Dm755 neodon-hostctl ~/.local/bin/neodon-hostctl" \
  || install -Dm755 "$BIN/neodon-hostctl" "$HOME/.local/bin/neodon-hostctl"
dry "install -Dm644 neodon-vpn.py ~/AI/neodon-vpn/neodon-vpn.py" \
  || install -Dm644 "$GUI_SRC" "$HOME/AI/neodon-vpn/neodon-vpn.py"
dry "copy profiles/*.json + icons + flags (no overwrite of live config)" || {
  for p in "$SRC"/profiles/*.json; do
    [ -e "$p" ] || continue
    cp -n "$p" "$HOME/AI/singbox/profiles/" 2>/dev/null || true
  done
  cp -rn "$SRC/icons/." "$HOME/AI/neodon-vpn/icons/" 2>/dev/null || true
  cp -rn "$SRC/flags/." "$HOME/AI/neodon-vpn/flags/" 2>/dev/null || true
}
# never overwrite user secrets/configs on reinstall
dry "copy config examples only if absent" || {
  for c in config.json config-full.json config-proxy.json; do
    [ -f "$HOME/AI/singbox/$c" ] || cp -n "$SRC/examples/$c.example" "$HOME/AI/singbox/$c" 2>/dev/null || true
  done
  chmod 600 "$HOME"/AI/singbox/*.json 2>/dev/null || true
}

# 2. systemd user units (vpn must survive reboots; GUI stays manual)
if ls "$SRC"/systemd/*.service >/dev/null 2>&1; then
  dry "install user units + daemon-reload" || {
    mkdir -p ~/.config/systemd/user
    cp "$SRC"/systemd/*.service ~/.config/systemd/user/
    systemctl --user daemon-reload
  }
fi
if ! loginctl show-user "$USER" 2>/dev/null | grep -q "Linger=yes"; then
  log "enabling linger (needs sudo once):"
  dry "sudo loginctl enable-linger $USER" || sudo loginctl enable-linger "$USER"
fi

# 3. sudoers allowlist (least privilege for shipped installs)
if [ -f "$SRC/sudoers.d/neodon-vpn.template" ]; then
  if sudo -n true 2>/dev/null; then
    dry "install/validate /etc/sudoers.d/neodon-vpn" || {
      sed "s/@USER@/$USER/g" "$SRC/sudoers.d/neodon-vpn.template" | sudo tee /etc/sudoers.d/neodon-vpn >/dev/null
      sudo chmod 440 /etc/sudoers.d/neodon-vpn
      sudo visudo -c || { echo "sudoers INVALID, rolled back" >&2; sudo rm -f /etc/sudoers.d/neodon-vpn; exit 4; }
    }
  else
    log "skip sudoers (no passwordless sudo): run the sudo steps manually."
  fi
fi

# 4. desktop file + steam shortcut (optional, never fatal)
if [ -f "$SRC/desktop/io.neodon.gui.desktop" ]; then
  dry "install desktop file" \
    || install -Dm644 "$SRC/desktop/io.neodon.gui.desktop" "$HOME/.local/share/applications/io.neodon.gui.desktop"
else
  log "desktop file not in package, keeping existing."
fi
if command -v steamos-add-to-steam >/dev/null 2>&1; then
  if [ -f ~/.local/share/neodon-steam-shortcut.done ]; then
    log "steam shortcut already registered, skipping (no duplicates)."
  else
    dry "steamos-add-to-steam desktop file" \
      || steamos-add-to-steam "$HOME/.local/share/applications/io.neodon.gui.desktop" >/dev/null 2>&1 || true
    touch ~/.local/share/neodon-steam-shortcut.done 2>/dev/null || true
  fi
fi

# 5. decky drop-in (optional, never fatal)
if [ -d ~/homebrew/plugins ] && [ -d "$SRC/decky/neodon-vpn" ]; then
  dry "decky plugin drop-in" || cp -r "$SRC/decky/neodon-vpn" ~/homebrew/plugins/
else
  log "decky: skipped (no plugins dir or no decky/ in tarball)."
fi

log "running verify..."
dry "bash $SRC/verify.sh" || bash "$SRC/verify.sh"
