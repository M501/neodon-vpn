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


def test_no_desktop_notify_on_connected(monkeypatch):
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
    assert calls == [], "no desktop spam, pill is the signal"


def test_state_hysteresis_holds_connected(monkeypatch):
    import json as _json
    m = app()
    win = _make_win(m, monkeypatch)
    win._status_loaded(_json.dumps({"actual_state": "CONNECTED", "desired_mode": "smart"}))
    win._status_loaded(_json.dumps({"actual_state": "DEGRADED", "desired_mode": "smart"}))
    assert win.state == "CONNECTED", "1st blip must not flap the pill"
    win._status_loaded(_json.dumps({"actual_state": "DEGRADED", "desired_mode": "smart"}))
    assert win.state == "CONNECTED", "2nd blip must not flap the pill"
    assert getattr(win, "_epoch", None) is not None
    win._status_loaded(_json.dumps({"actual_state": "DEGRADED", "desired_mode": "smart"}))
    assert win.state == "DEGRADED", "3rd miss adopts"
    assert win._epoch is None


def test_hard_states_apply_immediately(monkeypatch):
    import json as _json
    m = app()
    win = _make_win(m, monkeypatch)
    win._status_loaded(_json.dumps({"actual_state": "CONNECTED", "desired_mode": "smart"}))
    win._status_loaded(_json.dumps({"actual_state": "OFF", "desired_mode": "off"}))
    assert win.state == "OFF"
    win._status_loaded(_json.dumps({"actual_state": "CONNECTED", "desired_mode": "smart"}))
    win._status_loaded(_json.dumps({"actual_state": "FAILED", "desired_mode": "smart"}))
    assert win.state == "FAILED"


def test_desired_change_bypasses_hysteresis(monkeypatch):
    import json as _json
    m = app()
    win = _make_win(m, monkeypatch)
    win._status_loaded(_json.dumps({"actual_state": "CONNECTED", "desired_mode": "smart"}))
    win._status_loaded(_json.dumps({"actual_state": "TRANSITIONING", "desired_mode": "proxy"}))
    assert win.state == "TRANSITIONING", "user switch must show at once"


def test_transition_journal_appends(monkeypatch, tmp_path):
    import json as _json
    m = app()
    monkeypatch.setattr(m, "STATE_DIR", str(tmp_path))
    win = _make_win(m, monkeypatch)
    win._status_loaded(_json.dumps({"actual_state": "CONNECTING", "desired_mode": "smart"}))
    win._status_loaded(_json.dumps({"actual_state": "CONNECTED", "desired_mode": "smart", "exit_ip": "9.9.9.9"}))
    log = (tmp_path / "transitions.log").read_text()
    assert "->CONNECTING" in log and "->CONNECTED" in log, log


def test_polls_dont_rehighlight_mid_toggle(monkeypatch):
    import json as _json
    m = app()
    win = _make_win(m, monkeypatch)
    win.set_mode("smart")
    assert win.btn_proxy.isChecked()
    win._op_in_progress = True
    win._status_loaded(_json.dumps({"actual_state": "TRANSITIONING", "desired_mode": "full"}))
    assert win.btn_proxy.isChecked(), "stale poll must not flip highlight mid-toggle"
    assert not win.btn_tunnel.isChecked()
    win._op_in_progress = False
    win._status_loaded(_json.dumps({"actual_state": "TRANSITIONING", "desired_mode": "full"}))
    assert win.btn_tunnel.isChecked(), "backend truth applies after op"


def test_power_settle_ignores_double_tap(monkeypatch):
    import time as _t
    m = app()
    win = _make_win(m, monkeypatch)
    win.set_state("OFF")
    calls = []
    win.toggle = lambda mode: calls.append(mode)
    win._settle_until = _t.monotonic() + 5
    win.on_power()
    assert calls == [], "tap right after OFF must not re-enable"
    win._settle_until = 0
    win.on_power()
    assert calls == [win.mode], "deliberate press still works"


def test_busy_off_queues_and_drains(monkeypatch):
    m = app()
    win = _make_win(m, monkeypatch)
    win.set_state("CONNECTED")
    win.connected = True
    calls = []
    win.toggle = lambda mode: calls.append(mode)
    win._op_in_progress = True
    win.on_power()
    assert calls == [], "busy off-press must not run yet"
    assert win._pending == ("toggle", ("off",)), win._pending
    win._op_in_progress = False
    win._toggle_done(True, "ok")
    assert calls == ["off"], "queued off must run after op"
    assert win._pending is None


def test_pending_last_wins(monkeypatch):
    m = app()
    win = _make_win(m, monkeypatch)
    win.set_state("CONNECTED")
    win.connected = True
    win.toggle = lambda mode: None
    win.mode = "full"
    win._op_in_progress = True
    win.on_power()
    assert win._pending == ("toggle", ("off",))
    win._settle_until = 0
    win.set_mode("smart", restart=True)
    assert win._pending == ("toggle", ("smart",)), win._pending


def test_use_preset_toggle_routes(monkeypatch):
    m = app()
    win = _make_win(m, monkeypatch)
    calls = []

    def _sel(pid):
        calls.append(pid)
        win.active_profile = pid

    win.select_preset = _sel
    win.active_profile = "ru-bez-vpn"
    win.on_use_preset(False)
    assert calls == ["default"]
    assert win._last_preset == "ru-bez-vpn"
    win.on_use_preset(True)
    assert calls == ["default", "ru-bez-vpn"]


def test_active_preset_highlighted(monkeypatch):
    m = app()
    win = _make_win(m, monkeypatch)
    win.active_profile = "ru-bez-vpn"
    win.render_presets()
    b, _rb = win.preset_btns["ru-bez-vpn"]
    assert b.objectName() == "rowCardActive"
    for pid, (_bb, _r) in win.preset_btns.items():
        if pid != "ru-bez-vpn":
            assert _bb.objectName() == "rowCard"
    assert win.use_preset_cb.isChecked()
    win.active_profile = "default"
    win.render_presets()
    assert not win.use_preset_cb.isChecked()


def test_preset_summary_counts():
    m = app()
    s = m.preset_summary(["geosite:category-ru", "domain:avito.st"], ["geosite:youtube"])
    assert "2 зап." in s and "1 зап." in s
    assert "category-ru" in s and "youtube" in s
    assert m.preset_summary([], []) == "без доп. записей"


def test_preset_icon_fallback():
    m = app()
    fp, fb = m.preset_icon("ru-bez-vpn")
    assert fb == "🇷🇺"
    assert fp == "" or fp.endswith(("ru-bez-vpn.jpg", "ru-bez-vpn.png"))
    assert m.preset_icon("nope") == ("", "?")


def test_active_tag_visibility(monkeypatch):
    m = app()
    win = _make_win(m, monkeypatch)
    opened = []
    real_exec = m.QDialog.exec
    monkeypatch.setattr(m.QDialog, "exec", lambda self: opened.append(self) or 0)
    win.active_profile = "ru-bez-vpn"
    win.preset_details("ru-bez-vpn")
    assert len(opened) == 1
    texts = [l.text() for l in opened[0].findChildren(m.QLabel)]
    assert any("category-ru" in t for t in texts), texts
    assert any("АКТИВЕН" in t for t in texts), texts
    assert any("проверено вживую" in t for t in texts), texts
    monkeypatch.setattr(m.QDialog, "exec", real_exec)


def test_traffic_cards_render(monkeypatch, tmp_path):
    m = app()
    win = _make_win(m, monkeypatch)
    win.navigate("traffic")
    out = str(tmp_path / "traffic.png")
    assert win.pages["traffic"].grab().save(out), "grab failed"
    print("TRAFFIC-PNG:" + out)
