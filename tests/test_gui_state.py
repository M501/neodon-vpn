#!/usr/bin/env python3
"""Pill vs session-timer contract (offscreen; part of the pytest suite).

Regression for the owner's report: "connected, timer running, then Not connected
while the timer kept counting for another ~20 s". Root cause was that the timer base
was cleared only on the hysteresis path, so every hard transition (explicit OFF,
FAILED, LOCKED) left the counter running under "Not connected".

Contract pinned here (and by tests/test_gui_logic.py):
  * soft states (CONNECTING/STARTING/DEGRADED/TRANSITIONING) are debounced: 3 misses;
  * hard states (OFF/FAILED/LOCKED) and a user-changed desired apply immediately;
  * the timer base exists IF AND ONLY IF the state is CONNECTED — it clears in the
    same step whatever path flipped the state.

Standalone: QT_QPA_PLATFORM=offscreen python3 tests/test_gui_state.py [path/to/neodon-vpn.py]
"""
import importlib.util
import json
import os
import sys

if not (os.environ.get("WAYLAND_DISPLAY") or os.environ.get("DISPLAY")):
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

_arg = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1].endswith(".py") else None
APP = _arg or os.environ.get("NEODON_APP", "/home/m26/AI/neodon-vpn/neodon-vpn.py")

_mod = None
_win = None


def _app():
    global _mod
    if _mod is None:
        if not os.path.exists(APP):
            try:
                import pytest
                pytest.skip("GUI source not mounted at %s" % APP)
            except ImportError:
                print("GUI source not mounted at %s" % APP)
                sys.exit(0)
        spec = importlib.util.spec_from_file_location("neodon_vpn_app", APP)
        _mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(_mod)
    return _mod


class _Sig(object):
    """Tiny stand-in for a Qt signal (same pattern as tests/test_gui_logic.py)."""

    def __init__(self):
        self._slots = []

    def __get__(self, obj, objtype=None):     # pragma: no cover - never bound
        return self

    def connect(self, slot):
        self._slots.append(slot)

    def emit(self, *a):
        for slot in list(self._slots):
            slot(*a)


class _InertWorker(object):
    """Inert stand-in for CmdWorker: records creation, never emits."""

    created = 0

    def __init__(self, *a, **k):
        _InertWorker.created += 1
        s = _Holder()
        self.ok = s.ok
        self.fail = s.fail

    def start(self):
        pass

    def wait(self, ms=0):
        return True


class _Holder(object):
    def __init__(self):
        self.ok = _Sig()
        self.fail = _Sig()


def _window(monkeypatch=None):
    """Fresh MainWindow with the backend stubbed out (no subprocesses, no network).

    Same harness as tests/test_gui_logic.py: a real window would shell out to the
    backend on construction, which a unit test must not do.
    """
    from PySide6.QtWidgets import QApplication
    QApplication.instance() or QApplication([])
    m = _app()
    if monkeypatch is not None:
        monkeypatch.setattr(m, "CmdWorker", _InertWorker)
        monkeypatch.setattr(m, "run_cmd", lambda cmd, timeout=20: (0, "{}", ""))
        monkeypatch.setattr(m, "load_servers", lambda: [])
    win = m.MainWindow()
    # a test run must never write into the real transition logs
    win._log_transition = lambda *a, **k: None
    win._journal_transition = lambda *a, **k: None
    return win


def _doc(state, desired="smart"):
    return json.dumps({
        "desired_mode": desired, "profile": "default", "actual_state": state,
        "service": "sing-box", "service_state": "active", "firewall_rules": 0,
        "tun0": state == "CONNECTED", "exit_ip": "1.2.3.4" if state == "CONNECTED" else None,
        "server_tag": None, "latency_ms": 12, "watchdog_status": "ok",
        "consecutive_failures": 0, "next_retry": None,
    })


def _reset(win, state="OFF"):
    win.state = state
    win.connected = state == "CONNECTED"
    win._epoch = None
    win._off_streak = 0
    win._last_desired = "smart"
    return win


def _feed(win, state, desired="smart"):
    win._status_loaded(_doc(state, desired))


def _timer_agrees(win):
    """The invariant: the timer base exists iff the state is CONNECTED."""
    if win.state == "CONNECTED":
        return getattr(win, "_epoch", None) is not None
    return getattr(win, "_epoch", None) is None


def test_soft_states_are_debounced_and_the_timer_follows(monkeypatch):
    win = _reset(_window(monkeypatch))

    _feed(win, "CONNECTED")
    assert win.state == "CONNECTED" and win.connected is True
    assert _timer_agrees(win)

    _feed(win, "DEGRADED")
    assert win.state == "CONNECTED", "1st soft miss must not flap the pill"
    assert _timer_agrees(win)
    _feed(win, "TRANSITIONING")
    assert win.state == "CONNECTED", "2nd soft miss must not flap the pill"
    assert _timer_agrees(win)
    _feed(win, "DEGRADED")
    assert win.state == "DEGRADED", "3rd miss is believed"
    assert _timer_agrees(win), "adopting DEGRADED must clear the session timer"

    _feed(win, "CONNECTED")
    assert win.state == "CONNECTED" and _timer_agrees(win)


def test_hard_states_apply_at_once_and_clear_the_timer(monkeypatch):
    win = _reset(_window(monkeypatch))
    _feed(win, "CONNECTED")
    assert _timer_agrees(win)

    for raw, desired in (("OFF", "off"), ("FAILED", "smart"), ("LOCKED", "smart")):
        _reset(win)
        _feed(win, "CONNECTED")
        assert _timer_agrees(win)
        _feed(win, raw, desired=desired)
        assert win.state == raw, "%s must be shown immediately" % raw
        assert _timer_agrees(win), "%s left the session timer counting" % raw


# --- standalone runner (no pytest) -------------------------------------------
class _MP(object):
    """Minimal monkeypatch stand-in for the standalone run."""

    def setattr(self, obj, name, value):
        setattr(obj, name, value)


if __name__ == "__main__":
    checks = [test_soft_states_are_debounced_and_the_timer_follows,
              test_hard_states_apply_at_once_and_clear_the_timer]
    bad = 0
    print("GUI under test:", APP)
    for fn in checks:
        try:
            fn(_MP())
            print("PASS %s" % fn.__name__)
        except AssertionError as exc:
            bad += 1
            print("FAIL %s: %s" % (fn.__name__, exc))
    print("\n%d checks, %d failed" % (len(checks), bad))
    sys.exit(1 if bad else 0)
