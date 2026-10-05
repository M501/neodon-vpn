#!/usr/bin/env python3
"""State-machine regression test for the desktop GUI (offscreen, no device needed).

Runs the real MainWindow against synthetic status documents so the pill and the
session timer cannot contradict each other again (the owner's report: "connected,
timer running, then Not connected while the timer kept counting").

Usage (on a host with PySide6):
    QT_QPA_PLATFORM=offscreen python3 tests/test_gui_state.py [path/to/neodon-vpn.py]
Exit code 0 = all checks passed.
"""
import importlib.util
import json
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
_arg = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1].endswith(".py") else None
sys.argv = [sys.argv[0]]

from PySide6.QtWidgets import QApplication  # noqa: E402

GUI = _arg or os.environ.get("NEODON_GUI") or os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "neodon-vpn.py")

app = QApplication([])
spec = importlib.util.spec_from_file_location("neodon_gui", GUI)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

win = mod.MainWindow()
# never pollute the real logs from a test run
win._log_transition = lambda *a, **k: None
win._journal_transition = lambda *a, **k: None

FAILS = []
CHECKS = [0]


def doc(state, desired="smart", exit_ip="1.2.3.4"):
    return json.dumps({
        "desired_mode": desired, "profile": "default", "actual_state": state,
        "service": "sing-box", "service_state": "active", "firewall_rules": 0,
        "tun0": state == "CONNECTED", "exit_ip": exit_ip if state == "CONNECTED" else None,
        "server_tag": win.selected_tag or None, "latency_ms": 12,
        "watchdog_status": "ok", "consecutive_failures": 0, "next_retry": None,
    })


def check(label, cond, extra=""):
    CHECKS[0] += 1
    if cond:
        print("PASS %s" % label)
    else:
        print("FAIL %s %s" % (label, extra))
        FAILS.append(label)


def feed(state, desired="smart"):
    win._status_loaded(doc(state, desired))


def invariant(where):
    """The pill and the timer must never contradict each other."""
    if win.state == "CONNECTED":
        check("%s: CONNECTED keeps a session timer base" % where,
              getattr(win, "_epoch", None) is not None,
              "epoch=%r" % getattr(win, "_epoch", None))
    else:
        check("%s: %s clears the session timer base" % (where, win.state),
              getattr(win, "_epoch", None) is None,
              "epoch=%r" % getattr(win, "_epoch", None))


print("GUI under test:", GUI)
win.state = "OFF"
win.connected = False
win._epoch = None
win._off_streak = 0
win._last_desired = "smart"

# 1) connect
feed("CONNECTED")
check("connect: pill is CONNECTED", win.state == "CONNECTED", win.state)
check("connect: connected flag set", win.connected is True)
invariant("after connect")

# 2) one bad poll must not flip the pill while the timer runs
feed("OFF")
check("single OFF poll: still CONNECTED", win.state == "CONNECTED", win.state)
invariant("after 1 bad poll")
feed("DEGRADED")
check("single DEGRADED poll: still CONNECTED", win.state == "CONNECTED", win.state)
invariant("after 2 bad polls")

# 3) third contradiction is believed, and the timer base clears in the same step
feed("OFF")
check("third contradicting poll flips to OFF", win.state == "OFF", win.state)
invariant("after 3 bad polls")

# 4) recovery
feed("CONNECTED")
check("recovery: back to CONNECTED", win.state == "CONNECTED", win.state)
invariant("after recovery")

# 5) an explicit user OFF (desired changed) lands immediately
feed("OFF", desired="off")
check("explicit OFF lands at once", win.state == "OFF", win.state)
invariant("after explicit OFF")

# 6) LOCKED is a hard state: never debounced
feed("CONNECTED")
feed("LOCKED")
check("LOCKED is shown immediately", win.state == "LOCKED", win.state)
invariant("after LOCKED")
feed("CONNECTED", desired="full")
check("locked -> connected again", win.state == "CONNECTED", win.state)
invariant("after unlock")

# 7) FAILED also needs confirmation (a dead server must not flap on one poll).
#    The desired mode must NOT change here, otherwise the explicit-intent bypass
#    (correctly) takes effect immediately.
feed("FAILED", desired="full")
check("single FAILED poll: still CONNECTED", win.state == "CONNECTED", win.state)
invariant("after 1 FAILED poll")

win.deleteLater()
print("\n%d checks, %d failed" % (CHECKS[0], len(FAILS)))
sys.exit(1 if FAILS else 0)
