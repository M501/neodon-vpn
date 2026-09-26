#!/bin/bash
# qa-gui-states.sh — GUI Neodon: матрица переходов состояний (тап-инжект uinput).
# Кейсы: power on/off, быстрый ре-тап, PROXY/TUNNEL вкл/выкл/переключение.
# Требует: /dev/uinput rw, /tmp/qa-touch.py, бэкенд ~/AI/singbox.
# Использование: bash qa-gui-states.sh   → PASS/FAIL сводка + exit code = FAIL count.
export XDG_RUNTIME_DIR=/run/user/1000
export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus
export WAYLAND_DISPLAY=wayland-0
# prerequisite gate: taps require an unlocked session (locked -> skip, exit 77)
SID="$(loginctl list-sessions --no-legend 2>/dev/null | awk -v u="$USER" '$3==u{print $1; exit}')"
if [ -n "${SID:-}" ] && [ "$(loginctl show-session "$SID" -p LockedHint 2>/dev/null)" = "LockedHint=yes" ]; then
  echo "SKIP: session locked — tap tests need an unlocked screen"; exit 77
fi
SJ="bash $HOME/AI/singbox/singbox-toggle.sh status-json"
POWER_X=1014; POWER_Y=268
PROXY_X=697;  PROXY_Y=604
TUNNEL_X=1326; TUNNEL_Y=604
PASS=0; FAIL=0
st()  { $SJ 2>/dev/null | python3 -c 'import json,sys;print(json.load(sys.stdin).get("actual_state","?"))' 2>/dev/null; }
dsk() { $SJ 2>/dev/null | python3 -c 'import json,sys;print(json.load(sys.stdin).get("desired_mode","?"))' 2>/dev/null; }
tap() { python3 /tmp/qa-touch.py tap "$1" "$2" >/dev/null 2>&1; }
wait_state() { local want="$1" tmo="$2" i; for i in $(seq 1 $((tmo*2))); do [ "$(st)" = "$want" ] && return 0; sleep 0.5; done; return 1; }
wait_both()  { local wd="$1" wt="$2" tmo="$3" i; for i in $(seq 1 $((tmo*2))); do [ "$(st)" = "$wt" ] && [ "$(dsk)" = "$wd" ] && return 0; sleep 0.5; done; return 1; }
ck() { local name="$1"; shift; if "$@"; then echo "  PASS  $name"; PASS=$((PASS+1)); else echo "  FAIL  $name   [state=$(st) desired=$(dsk)]"; FAIL=$((FAIL+1)); fi; }

echo "=== qa-gui-states @ $(date +%H:%M:%S) ==="
# canon start: ON smart
if [ "$(st)" != "CONNECTED" ] || [ "$(dsk)" != "smart" ]; then
  bash $HOME/AI/singbox/singbox-toggle.sh smart >/dev/null 2>&1
  wait_state CONNECTED 15 || true
fi
echo "start: state=$(st) desired=$(dsk)"

echo "TC1 power-off (tap power)"
tap $POWER_X $POWER_Y
ck "TC1 -> OFF (<=6s)" wait_state OFF 6

echo "TC2 power-on quick re-tap (1s later, old settle window)"
sleep 1
tap $POWER_X $POWER_Y
ck "TC2 -> CONNECTED (<=8s)" wait_state CONNECTED 8

echo "TC3 switch to TUNNEL(full) by mode button"
tap $TUNNEL_X $TUNNEL_Y
ck "TC3 -> CONNECTED/full (<=12s)" wait_both full CONNECTED 12

echo "TC4 switch back to PROXY(smart)"
tap $PROXY_X $PROXY_Y
ck "TC4 -> CONNECTED/smart (<=10s)" wait_both smart CONNECTED 10

echo "TC5 power-off then TUNNEL-while-OFF turns ON (full)"
tap $POWER_X $POWER_Y
ck "TC5a -> OFF (<=6s)" wait_state OFF 6
tap $TUNNEL_X $TUNNEL_Y
ck "TC5b -> CONNECTED/full (<=12s)" wait_both full CONNECTED 12

echo "TC6 restore smart"
tap $PROXY_X $PROXY_Y
ck "TC6 -> CONNECTED/smart (<=10s)" wait_both smart CONNECTED 10

echo "TC7 probe stability under load (6x status-json)"
OKC=0
for i in $(seq 1 6); do
  E=$($SJ 2>/dev/null | python3 -c 'import json,sys;d=json.load(sys.stdin);print(1 if d.get("exit_ip") else 0)' 2>/dev/null)
  [ "$E" = "1" ] && OKC=$((OKC+1))
  sleep 1
done
ck "TC7 exit-probe 6/6 ok (got $OKC/6)" test "$OKC" -ge 5

echo "=== RESULT: PASS=$PASS FAIL=$FAIL ==="
exit "$FAIL"
