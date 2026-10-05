#!/bin/bash
# Edge cases: GUI restart while connected, rapid power double-press, final clean state.
set -u
export XDG_RUNTIME_DIR=/run/user/1000
export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus
export WAYLAND_DISPLAY=wayland-0
export DISPLAY=:0
HOOK=/home/m26/AI/neodon-vpn/gui-action.json
SB=/home/m26/AI/singbox
GUIF=/home/m26/AI/neodon-vpn/neodon-vpn.py

hookj() { printf '%s' "$1" > "$HOOK"; sleep 1; }
st() {
  rm -f /tmp/appstate.json
  hookj '{"action":"state","path":"/tmp/appstate.json"}'
  sleep 0.6
  python3 - /tmp/appstate.json <<'PY'
import json, os, sys
try:
    app = json.load(open(sys.argv[1]))
except Exception as exc:
    print("app state unreadable:", exc); raise SystemExit(0)
be = {}
try:
    import subprocess
    out = subprocess.run(["bash", os.path.expanduser("~/AI/singbox/singbox-toggle.sh"), "status-json"],
                         capture_output=True, text=True, timeout=25).stdout.strip().splitlines()
    be = json.loads(out[-1]) if out else {}
except Exception:
    pass
bad = []
if app.get("state") == "CONNECTED" and not app.get("epoch_set"):
    bad.append("pill=CONNECTED but no timer base")
if app.get("state") != "CONNECTED" and app.get("epoch_set"):
    bad.append("pill=%s but timer base alive" % app.get("state"))
if app.get("state") != "CONNECTED" and app.get("timer") not in (None, "00:00:00"):
    bad.append("pill=%s but timer=%s" % (app.get("state"), app.get("timer")))
print("app:%-13s timer=%-9s epoch=%-5s op=%-5s pending=%-5s | backend:%-12s exit=%s %s" % (
    app.get("state"), app.get("timer"), app.get("epoch_set"), app.get("op_in_progress"),
    bool(app.get("pending")), be.get("actual_state"), be.get("exit_ip"),
    ("  !! " + "; ".join(bad)) if bad else "OK"))
PY
}

echo "=== E1: connect ==="
hookj '{"action":"toggle"}'
for i in 1 2 3 4 5; do sleep 4; st; done

echo "=== E2: restart the GUI while connected (state must survive) ==="
for p in /proc/[0-9]*; do
  pid=${p#/proc/}
  if tr '\0' ' ' < "$p/cmdline" 2>/dev/null | grep -q "AI/neodon-vpn/neodon-vpn.py"; then kill "$pid" 2>/dev/null; fi
done
sleep 3
systemd-run --user --unit=neodon-gui-live --collect \
  --setenv=XDG_RUNTIME_DIR=/run/user/1000 \
  --setenv=DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus \
  --setenv=WAYLAND_DISPLAY=wayland-0 --setenv=DISPLAY=:0 \
  --setenv=QT_QPA_PLATFORMTHEME=kde \
  /usr/bin/python3 "$GUIF" >/dev/null 2>&1
sleep 8
echo "fresh GUI pid: $(pgrep -f 'AI/neodon-vpn/neodon-vpn.py' | head -1)"
st

echo "=== E3: rapid double press of power (300 ms apart) ==="
printf '{"action":"toggle"}' > "$HOOK"
sleep 0.3
printf '{"action":"toggle"}' > "$HOOK"
sleep 1
for i in 1 2 3 4 5 6; do sleep 4; st; done

echo "=== E4: settle + leave the owner's state (OFF) ==="
if [ "$(cat "$SB/.mode")" != "off" ]; then
  hookj '{"action":"toggle"}'
  sleep 8
fi
for i in 1 2 3; do sleep 3; st; done

echo "=== E5: leftovers check (must be clean) ==="
echo "mode: $(cat "$SB/.mode")"
echo "prio-20 REJECT rules: $(sudo -n firewall-cmd --direct --get-all-rules 2>/dev/null | grep -c 'filter OUTPUT_direct 20 ' || true)"
echo "resolv.conf: $(head -1 /etc/resolv.conf)"
echo "tun0: $(ip link show tun0 2>/dev/null | head -1 || echo none)"
echo "units: $(systemctl --user is-active sing-box.service sing-box-full.service sing-box-proxy.service 2>&1 | tr '\n' ' ')"
echo "exit ip (ISP): $(curl -s -m 8 https://api.ipify.org 2>/dev/null || echo FAIL)"
echo "no-op pending in app: $(grep -o '"pending": [^,]*' /tmp/appstate.json)"
