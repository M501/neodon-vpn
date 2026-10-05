#!/bin/bash
# Route walker: the paths any sane user takes, with consistency checks between the
# pill, the session timer and the backend status document.
set -u
export XDG_RUNTIME_DIR=/run/user/1000
export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus
WAYLAND_DISPLAY=wayland-0
DISPLAY=:0
export WAYLAND_DISPLAY DISPLAY
HOOK=/home/m26/AI/neodon-vpn/gui-action.json
SB=/home/m26/AI/singbox
LOG=/home/m26/qa_route.log
: > "$LOG"

hook() { printf '{"action":"%s"}' "$1" > "$HOOK"; sleep 1; }
hookj() { printf '%s' "$1" > "$HOOK"; sleep 1; }

st() {  # one consistency snapshot
  rm -f /tmp/appstate.json
  hookj '{"action":"state","path":"/tmp/appstate.json"}'
  sleep 0.6
  app=$(cat /tmp/appstate.json 2>/dev/null || echo '{}')
  be=$(timeout 15 bash "$SB/singbox-toggle.sh" status-json 2>/dev/null | tail -1)
  py=$(python3 - "$app" "$be" <<'PY'
import json, sys
app = json.loads(sys.argv[1] or "{}")
be = json.loads(sys.argv[2] or "{}")
st = app.get("state"); timer = app.get("timer"); ep = app.get("epoch_set")
raw = be.get("actual_state"); mode = be.get("desired_mode")
bad = []
if st == "CONNECTED" and not ep:
    bad.append("pill=CONNECTED but no timer base")
if st != "CONNECTED" and ep and st != "TRANSITIONING":
    bad.append("pill=%s but timer base alive" % st)
if st != "CONNECTED" and timer not in (None, "00:00:00") and st != "TRANSITIONING":
    bad.append("pill=%s but timer=%s" % (st, timer))
print("app:%-13s timer=%-9s epoch=%-5s | backend:%-12s desired=%-7s exit=%s %s" % (
    st, timer, ep, raw, mode, be.get("exit_ip"), ("  !! " + "; ".join(bad)) if bad else "OK"))
PY
)
  echo "$py" | tee -a "$LOG"
}

echo "=== R1: fresh OFF state ==="
st

echo "=== R2: press CONNECT (power) ==="
hookj '{"action":"toggle"}'
for i in 1 2 3 4 5 6; do sleep 4; st; done

echo "=== R3: watch 40 s for flapping (pill/timer/backend) ==="
for i in $(seq 1 10); do sleep 4; st; done

echo "=== R4: switch server while CONNECTED (idx 3) ==="
hookj '{"action":"server","idx":3}'
sleep 6
st
echo "exit ip now: $(curl -s -m 8 https://api.ipify.org 2>/dev/null || echo FAIL)"

echo "=== R5: switch mode while CONNECTED (PROXY -> TUNNEL) ==="
hookj '{"action":"set_mode","mode":"full"}'
sleep 14
st
echo "mode file: $(cat "$SB/.mode")"
hookj '{"action":"set_mode","mode":"smart"}'
sleep 14
st
echo "mode file: $(cat "$SB/.mode")"

echo "=== R6: refresh subscription while CONNECTED ==="
hookj '{"action":"refresh"}'
sleep 25
st

echo "=== R7: every page renders while CONNECTED ==="
for pg in settings apps traffic logs about home; do
  hookj "{\"action\":\"navigate\",\"page\":\"$pg\"}"
  sleep 1
  rm -f "/tmp/pg_$pg.png"
  hookj "{\"action\":\"grab\",\"path\":\"/tmp/pg_$pg.png\"}"
  sleep 1.5
  [ -s "/tmp/pg_$pg.png" ] && echo "page $pg: ok ($(stat -c%s "/tmp/pg_$pg.png") bytes)" | tee -a "$LOG" || echo "page $pg: FAIL" | tee -a "$LOG"
done

echo "=== R8: press DISCONNECT ==="
hookj '{"action":"toggle"}'
for i in 1 2 3 4; do sleep 4; st; done

echo "=== summary of the walker ==="
echo "state lines: $(grep -c "app:" "$LOG")   inconsistencies: $(grep -c '!!' "$LOG" || true)"
grep '!!' "$LOG" || echo "(no pill/timer/backend contradictions)"
echo
echo "=== transitions during the walk ==="
tail -12 /home/m26/AI/neodon-vpn/transitions.log
