#!/bin/bash
# neodon dns-fix: static resolv.conf -> TUN hijack-dns (sing-box sees every
# query, learns domain map, answers via DoT-through-proxy = no ISP poison).
# apply on smart/proxy/full, restore (stub symlink) on off. Idempotent.
RESOLV=/etc/resolv.conf
LINKBAK=/etc/resolv.conf.neodon.link
FILEBAK=/etc/resolv.conf.neodon.bak
MARK="# neodon-vpn static"
apply() {
  if grep -q "neodon-vpn static" "$RESOLV" 2>/dev/null; then echo "dns already neodon"; return 0; fi
  if [ -L "$RESOLV" ]; then
    readlink "$RESOLV" | sudo -n tee "$LINKBAK" >/dev/null
    sudo -n rm -f "$RESOLV"
  elif [ ! -f "$FILEBAK" ]; then
    sudo -n cp "$RESOLV" "$FILEBAK"
  fi
  printf '%s (via TUN hijack-dns)\nnameserver 1.1.1.1\n' "$MARK" | sudo -n tee "$RESOLV" >/dev/null
  echo "dns neodon ON"
}
restore() {
  if [ -f "$LINKBAK" ]; then
    sudo -n rm -f "$RESOLV"
    sudo -n ln -s "$(cat "$LINKBAK")" "$RESOLV"
    sudo -n rm -f "$LINKBAK" "$FILEBAK"
    echo "dns stub restored"
  elif [ -f "$FILEBAK" ]; then
    sudo -n cp "$FILEBAK" "$RESOLV"; sudo -n rm -f "$FILEBAK"
    echo "dns file restored"
  else echo "dns already stock"; fi
}
case "${1:-}" in apply) apply;; restore) restore;; *) echo "usage: $0 apply|restore"; exit 1;; esac
