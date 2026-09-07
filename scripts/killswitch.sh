#!/usr/bin/env bash
# Fail-closed egress kill-switch for the FULL tunnel (firewalld direct rules).
# install: resolve endpoint IPs FIRST (DNS still open), add-missing allowlist rules
#          (no flush on reinstall -> zero egress window), verify allowlist count,
#          REJECT LAST at prio 20. Any failure -> die; never declare active.
# remove:  drop the whole OUTPUT_direct chain (idempotent).
# verify:  preflight - every expected rule must be present, exit non-zero on FAIL.
set -u

CFG="$HOME/AI/singbox/config-full.json"
FW="sudo -n firewall-cmd --direct"

die() { echo "KILLSWITCH ERROR: $*" >&2; exit 1; }

endpoint_host() {
  python3 - "$CFG" <<'PY'
import json, sys
cfg = json.load(open(sys.argv[1]))
for o in cfg.get('outbounds', []):
    if o.get('tag') == 'proxy' and o.get('server'):
        print(o['server'])
        break
PY
}

ALLOW_RULES=(
  "ipv4 0 -o lo -j ACCEPT"
  "ipv6 0 -o lo -j ACCEPT"
  "ipv4 1 -o tun0 -j ACCEPT"
  "ipv6 1 -o tun0 -j ACCEPT"
  "ipv4 2 -d 192.168.0.0/16 -j ACCEPT"
  "ipv4 2 -d 172.16.0.0/12 -j ACCEPT"
  "ipv4 2 -d 10.0.0.0/8 -j ACCEPT"
  "ipv6 2 -d fc00::/7 -j ACCEPT"
  "ipv6 2 -d fe80::/10 -j ACCEPT"
  "ipv4 3 -p udp --sport 68 -j ACCEPT"
  "ipv6 3 -p udp --sport 546 -j ACCEPT"
  "ipv6 3 -p icmpv6 --icmpv6-type 133 -j ACCEPT"
  "ipv6 3 -p icmpv6 --icmpv6-type 135 -j ACCEPT"
  "ipv6 3 -p icmpv6 --icmpv6-type 136 -j ACCEPT"
  "ipv4 4 -p udp -d 1.1.1.1 --dport 53 -j ACCEPT"
  "ipv4 4 -p tcp -d 1.1.1.1 --dport 53 -j ACCEPT"
  "ipv4 4 -p udp -d 1.0.0.1 --dport 53 -j ACCEPT"
  "ipv4 4 -p tcp -d 1.0.0.1 --dport 53 -j ACCEPT"
)
REJECT_RULES=(
  "ipv4 20 -j REJECT"
  "ipv6 20 -j REJECT"
)

EXISTING=""
add_missing() {
  # $1=fam $2=prio, rest=rule args; skip if already present, die on add error
  local fam="$1" prio="$2"; shift 2
  local spec="$fam filter OUTPUT_direct $prio $*"
  if ! grep -qF -- "$spec" <<<"$EXISTING"; then
    $FW --add-rule $fam filter OUTPUT_direct $prio "$@" || die "add-rule failed: $spec"
    EXISTING="$EXISTING
$spec"
    echo "KILLSWITCH: added $spec"
  fi
}

install() {
  echo "KILLSWITCH: resolving endpoint (DNS still open)..."
  local hosts ips h ip
  hosts="$(endpoint_host || true)"
  hosts="${hosts:+$hosts
}u.neodon.net"
  ips="$(for h in $hosts; do getent ahostsv4 "$h" 2>/dev/null | awk '{print $1}'; done | sort -u)"
  if [ -z "$ips" ]; then
    die "endpoint resolution failed — refusing to lock down"
  fi
  echo "KILLSWITCH: endpoint -> $(echo $ips | tr '\n' ' ')"

  EXISTING="$($FW --get-all-rules 2>/dev/null || true)"
  # one-time migration: drop pre-narrowing broad DNS allows
  for broad in "ipv4 filter OUTPUT_direct 4 -d 1.1.1.1 -j ACCEPT" "ipv4 filter OUTPUT_direct 4 -d 1.0.0.1 -j ACCEPT"; do
    if grep -qF -- "$broad" <<<"$EXISTING"; then
      set -- $broad
      $FW --remove-rule "$1" filter OUTPUT_direct "$2" "${@:3}" 2>/dev/null || true
      EXISTING="$(echo "$EXISTING" | grep -vF -- "$broad" || true)"
    fi
  done
  # prune endpoint ACCEPTs that are no longer current (unbounded growth)
  for stale in $(echo "$EXISTING" | grep -o 'ipv4 filter OUTPUT_direct 5 -d [0-9.]* -j ACCEPT' | awk '{print $6}'); do
    keep=false
    for ip in $ips; do [ "$stale" = "$ip" ] && keep=true; done
    if [ "$keep" = false ]; then
      $FW --remove-rule ipv4 filter OUTPUT_direct 5 -d "$stale" -j ACCEPT 2>/dev/null || true
    fi
  done

  local r
  for r in "${ALLOW_RULES[@]}"; do
    set -- $r
    add_missing "$1" "$2" "${@:3}"
  done
  for ip in $ips; do
    add_missing ipv4 5 -d "$ip" -j ACCEPT
  done

  # verify allowlist BEFORE REJECT is added
  local n min
  n="$(echo "$EXISTING" | grep -c ' filter OUTPUT_direct ' || true)"
  min=$(( ${#ALLOW_RULES[@]} + $(echo "$ips" | wc -l) ))
  if [ "$n" -lt "$min" ]; then
    echo "KILLSWITCH ERROR: allowlist incomplete ($n rules < $min) — rolling back" >&2
    $FW --remove-rules ipv4 filter OUTPUT_direct 2>/dev/null || true
    $FW --remove-rules ipv6 filter OUTPUT_direct 2>/dev/null || true
    die "allowlist verification failed — firewall rolled back"
  fi

  # REJECT LAST: never install before the allowlist
  for r in "${REJECT_RULES[@]}"; do
    set -- $r
    add_missing "$1" "$2" "${@:3}"
  done
  n="$(echo "$EXISTING" | grep -c ' filter OUTPUT_direct ' || true)"
  echo "KILLSWITCH: locked ($n rules)"
}

remove() {
  # allows persist by design (harmless without REJECT); only REJECT is dynamic
  $FW --remove-rule ipv4 filter OUTPUT_direct 20 -j REJECT 2>/dev/null || true
  $FW --remove-rule ipv6 filter OUTPUT_direct 20 -j REJECT 2>/dev/null || true
  echo "KILLSWITCH: unlocked (allowlist persists)"
}

verify() {
  local fail=0 r ip
  for r in "${ALLOW_RULES[@]}" "${REJECT_RULES[@]}"; do
    set -- $r
    if $FW --query-rule "$1" filter OUTPUT_direct "$2" "${@:3}" >/dev/null 2>&1; then
      echo "PASS: $r"
    else
      echo "FAIL: $r"
      fail=1
    fi
  done
  local ips
  ips="$(for h in $(endpoint_host || true) u.neodon.net; do getent ahostsv4 "$h" 2>/dev/null | awk '{print $1}'; done | sort -u)"
  for ip in $ips; do
    if $FW --query-rule ipv4 filter OUTPUT_direct 5 -d "$ip" -j ACCEPT >/dev/null 2>&1; then
      echo "PASS: ipv4 5 -d $ip -j ACCEPT"
    else
      echo "FAIL: ipv4 5 -d $ip -j ACCEPT"
      fail=1
    fi
  done
  if [ "$fail" -ne 0 ]; then
    echo "KILLSWITCH: verify FAILED" >&2
    exit 1
  fi
  echo "KILLSWITCH: verify OK"
}

case "${1:-}" in
  install) install ;;
  remove)  remove ;;
  verify)  verify ;;
  *) echo "usage: $0 {install|remove|verify}" >&2; exit 2 ;;
esac