"""Neodon GUI logic tests — PRIMARY: Bazzite host (same machine/model that runs it).
Run on host: QT_QPA_PLATFORM=offscreen python3 -m pytest ~/AI/neodon-tests/test_gui_logic.py -v
Run on Windows venv (secondary): set NEODON_APP to local copy of neodon-vpn.py.
No network, no services, no GUI shown. ponytail: stdlib + pytest only.
"""
import importlib.util
import os

APP = os.environ.get("NEODON_APP", "/home/m26/AI/neodon-vpn/neodon-vpn.py")

_mod = None


def app():
    global _mod
    if _mod is None:
        spec = importlib.util.spec_from_file_location("neodon_vpn_app", APP)
        _mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(_mod)
    return _mod


def test_import():
    assert app() is not None


def test_sub_empty_gives_zero_total():
    m = app()
    info = m.parse_sub_info("")
    used, total = m.sub_used_total(info)
    assert total == 0


def test_sub_userinfo_line_parses():
    m = app()
    line = ("subscription-userinfo: upload=0; download=105654778160; "
            "total=161061273600; expire=1801345352")
    info = m.parse_sub_info(line)
    used, total = m.sub_used_total(info)
    assert (used, total) == (105654778160, 161061273600)


# --- T1b: target behavior for spec 001 (RED until implemented) ---
import sys as _sys

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication

_QAPP = QApplication.instance() or QApplication([])


class _Sig(QObject):
    ok = Signal(str)
    fail = Signal(str)


class FakeWorker:
    """Inert stand-in for CmdWorker: records creation, never emits."""
    created = 0

    def __init__(self, *a, **k):
        FakeWorker.created += 1
        self._s = _Sig()
        self.ok = self._s.ok
        self.fail = self._s.fail

    def start(self):
        pass

    def wait(self, ms=0):
        return True


def _make_win(m, monkeypatch):
    FakeWorker.created = 0
    monkeypatch.setattr(m, "CmdWorker", FakeWorker)
    monkeypatch.setattr(m, "run_cmd", lambda cmd, timeout=20: (0, "{}", ""))
    monkeypatch.setattr(m, "load_servers", lambda: [])
    return m.MainWindow()


def test_poll_single_flight_skips_while_busy(monkeypatch):
    m = app()
    win = _make_win(m, monkeypatch)
    FakeWorker.created = 0
    win._poll_busy = False
    win.poll_status()
    assert FakeWorker.created == 1
    win.poll_status()
    assert FakeWorker.created == 1, "second poll must be skipped while busy"
    assert getattr(win, "_poll_skipped", 0) >= 1


def test_set_state_binds_timer(monkeypatch):
    m = app()
    win = _make_win(m, monkeypatch)
    win.set_state("CONNECTED")
    assert getattr(win, "_epoch", None) is not None
    win.set_state("OFF")
    assert win._epoch is None
    assert win.timer_lbl.text() == "00:00:00"


def test_kinetic_single_touch_helper():
    src = open(APP, encoding="utf-8").read()
    assert src.count("grabGesture") == 1, "single helper owns the grab"
    assert "LeftMouseButtonGesture" not in src, "touch-only, taps must pass"
    assert src.count("def _enable_kinetic") == 1


def test_sub_empty_shows_reason_not_silent(monkeypatch, tmp_path):
    m = app()
    monkeypatch.setattr(m, "STATE_DIR", str(tmp_path))
    win = _make_win(m, monkeypatch)
    win._apply_sub_info("")
    assert win.sub_used.text() == "N/A"


def test_sub_empty_uses_cache(monkeypatch, tmp_path):
    import json as _json
    m = app()
    monkeypatch.setattr(m, "STATE_DIR", str(tmp_path))
    (tmp_path / "sub-cache.json").write_text(_json.dumps(
        {"pct": 13, "used": "20.1 GB / 150 GB",
         "expire": "Active until: 31 Jan 2027"}))
    win = _make_win(m, monkeypatch)
    win._apply_sub_info("")
    assert win.sub_used.text() == "20.1 GB / 150 GB (кэш)"


def test_epoch_survives_single_blip(monkeypatch):
    import json as _json
    m = app()
    win = _make_win(m, monkeypatch)
    win._status_loaded(_json.dumps({"actual_state": "CONNECTED"}))
    assert getattr(win, "_epoch", None) is not None
    win._status_loaded(_json.dumps({"actual_state": "DEGRADED"}))
    assert getattr(win, "_epoch", None) is not None, "1 blip must not reset timer"
    win._status_loaded(_json.dumps({"actual_state": "DEGRADED"}))
    win._status_loaded(_json.dumps({"actual_state": "DEGRADED"}))
    assert win._epoch is None, "3 misses clear the epoch"


def test_transitions_logged(monkeypatch):
    m = app()
    win = _make_win(m, monkeypatch)
    win.set_state("CONNECTED")
    win.set_state("OFF")
    tr = getattr(win, "_transitions", [])
    assert [t[2] for t in tr[-2:]] == ["CONNECTED", "OFF"]


def test_select_server_flow(monkeypatch, qtbot):
    m = app()
    win = _make_win(m, monkeypatch)
    monkeypatch.setattr(m, "run_cmd", lambda cmd, timeout=20: (0, "OK", ""))
    monkeypatch.setattr(win, "refresh_active_server", lambda: None)
    monkeypatch.setattr(win, "render_servers", lambda: None)
    win.servers = [{"address": "x.example", "remarks": "t"}]
    win.set_state("CONNECTED")
    win._select_server_idx(0)
    qtbot.waitUntil(lambda: not win._op_in_progress, timeout=5000)
    assert FakeWorker.created >= 1, "done must trigger status poll"


def test_clickframe_tap_fires(monkeypatch, qtbot):
    from PySide6.QtCore import QPoint, Qt
    from PySide6.QtTest import QTest
    m = app()
    _make_win(m, monkeypatch)
    hits = []
    fr = m._ClickFrame(lambda: hits.append(1))
    fr.resize(200, 60)
    fr.show()
    qtbot.mouseClick(fr, Qt.MouseButton.LeftButton, pos=QPoint(100, 30))
    assert hits == [1]


def test_clickframe_drag_no_fire(monkeypatch, qtbot):
    from PySide6.QtCore import QPoint, Qt
    from PySide6.QtTest import QTest
    m = app()
    _make_win(m, monkeypatch)
    hits = []
    fr = m._ClickFrame(lambda: hits.append(1))
    fr.resize(200, 60)
    fr.show()
    QTest.mousePress(fr, Qt.MouseButton.LeftButton, pos=QPoint(100, 30))
    QTest.mouseMove(fr, QPoint(160, 30))
    QTest.mouseRelease(fr, Qt.MouseButton.LeftButton, pos=QPoint(160, 30))
    assert hits == [], "scroll-release must not fire"


def test_toggle_optimistic(monkeypatch):
    m = app()
    win = _make_win(m, monkeypatch)
    win.set_state("OFF")
    win.toggle("smart")
    assert win._op_in_progress is True
    assert win.state == "TRANSITIONING"


def test_fast_poll_wanted():
    m = app()
    assert m._fast_poll_wanted("CONNECTING", 100.0, 90.0) is True
    assert m._fast_poll_wanted("DEGRADED", 100.0, 90.0) is True
    assert m._fast_poll_wanted("CONNECTED", 100.0, 90.0) is False
    assert m._fast_poll_wanted("CONNECTING", 100.0, 101.0) is False
    assert m._fast_poll_wanted("OFF", 100.0, 90.0) is False


def test_toggle_arms_fast_poll(monkeypatch):
    import time as _t
    m = app()
    win = _make_win(m, monkeypatch)
    win.set_state("OFF")
    win.toggle("smart")
    assert win._fast_poll_until > _t.monotonic()


def test_notify_on_connected_once(monkeypatch):
    import json as _json
    m = app()

    class _P:
        def __init__(self, *a, **k):
            calls.append(a)

    calls = []
    monkeypatch.setattr(m.subprocess, "Popen", _P)
    win = _make_win(m, monkeypatch)
    win.set_state("CONNECTING")
    win._status_loaded(_json.dumps({"actual_state": "CONNECTED", "exit_ip": "1.2.3.4"}))
    win._status_loaded(_json.dumps({"actual_state": "CONNECTED", "exit_ip": "1.2.3.4"}))
    assert len(calls) == 1, calls
