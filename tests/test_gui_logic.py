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
    assert win.sub_used.text() == "20.1 GB / 150 GB (cached)"


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
    b, _rb, _act = win.preset_btns["ru-bez-vpn"]
    assert b.objectName() == "rowCardActive"
    for pid, (_bb, _r, _a) in win.preset_btns.items():
        if pid != "ru-bez-vpn":
            assert _bb.objectName() == "rowCard"
    assert win.use_preset_cb.isChecked()
    win.active_profile = "default"
    win.render_presets()
    assert not win.use_preset_cb.isChecked()


def test_preset_summary_counts():
    m = app()
    s = m.preset_summary(["geosite:category-ru", "domain:avito.st"], ["geosite:youtube"])
    assert "direct: 2" in s and "via VPN: 1" in s
    assert "category-ru" in s and "youtube" in s
    assert m.preset_summary([], []) == "no extra rules"


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
    assert any("ACTIVE" in t for t in texts), texts
    assert any("verified live" in t for t in texts), texts
    monkeypatch.setattr(m.QDialog, "exec", real_exec)


def test_route_lookup(tmp_path):
    import json as _json
    m = app()
    cfg = tmp_path / "cfg.json"
    cfg.write_text(_json.dumps({"route": {
        "rules": [{"domain_suffix": ["example.ru"], "outbound": "direct"}],
        "final": "proxy"}}))
    assert m.route_lookup("a.example.ru", str(cfg))[0] == "direct"
    assert m.route_lookup("other.com", str(cfg))[0] == "proxy"
    assert m.route_lookup("x.com", str(tmp_path / "nope.json"))[0] == "?"


def test_dialog_canaries_live(monkeypatch):
    m = app()
    win = _make_win(m, monkeypatch)
    opened = []
    monkeypatch.setattr(m.QDialog, "exec", lambda self: opened.append(self) or 0)
    monkeypatch.setattr(m, "route_lookup",
                        lambda dom: {"ya.ru": ("direct", "suffix")}.get(dom, ("proxy", "final")))
    win.active_profile = "ru-bez-vpn"
    win.preset_details("ru-bez-vpn")
    texts = [l.text() for l in opened[0].findChildren(m.QLabel)]
    assert any("ya.ru → direct ✓" in t for t in texts), texts
    assert any("youtube.com → VPN ✓" in t for t in texts), texts


def test_card_active_tag(monkeypatch):
    m = app()
    win = _make_win(m, monkeypatch)
    win.active_profile = "ru-bez-vpn"
    win.render_presets()
    assert win.preset_btns["ru-bez-vpn"][2].isHidden() is False
    assert win.preset_btns["default"][2].isHidden() is True


def test_card_pixmap_missing():
    m = app()
    assert m.card_pixmap("/nonexistent/x.png") is None


def test_elided_minimum_allows_shrink():
    m = app()
    assert m._ElidedLabel("very long server name here").minimumSizeHint().width() == 0


def test_geom_roundtrip(monkeypatch, tmp_path):
    m = app()
    monkeypatch.setattr(m, "STATE_DIR", str(tmp_path))
    win = _make_win(m, monkeypatch)
    win.resize(700, 700)
    win._save_geom()
    win.resize(620, 680)
    win._restore_geom()
    assert (win.width(), win.height()) == (700, 700)
    import json as _json
    win.write_gui_state()
    assert "geom" in _json.loads((tmp_path / "gui-state.json").read_text())


def test_flag_code_brackets():
    m = app()
    assert m.flag_code("[PL] NEODON VPN x") == "PL"
    assert m.flag_code("no code here") is None


def test_tray_flag_and_mode(monkeypatch):
    m = app()
    win = _make_win(m, monkeypatch)
    calls = {}

    class _T:
        def setIcon(self, i):
            calls["icon"] = i

        def setToolTip(self, t):
            calls["tip"] = t

    win.tray = _T()
    win.mode = "smart"
    win.status = {"server_tag": "[PL] NEODON VPN x", "exit_ip": "1.1.1.1"}
    win._sync_tray("CONNECTED")
    assert "PROXY" in calls["tip"] and "NEODON" in calls["tip"], calls
    win.mode = "full"
    win._sync_tray("CONNECTED")
    assert "TUNNEL" in calls["tip"], calls


def test_tray_state_mirror(monkeypatch, tmp_path):
    import json as _json
    m = app()
    monkeypatch.setattr(m, "STATE_DIR", str(tmp_path))
    win = _make_win(m, monkeypatch)

    class _T:
        def setIcon(self, i):
            pass

        def setToolTip(self, t):
            pass

    win.tray = _T()
    win.mode = "smart"
    win.status = {"server_tag": "[PL] NEODON VPN x"}
    win._sync_tray("CONNECTED")
    d = _json.loads((tmp_path / "tray-state.json").read_text())
    assert d["state"] == "CONNECTED" and "PROXY" in d["tooltip"], d


def test_server_head_truncated(monkeypatch):
    m = app()
    win = _make_win(m, monkeypatch)
    win.servers = [{"remarks": "[RU2] YouTube без рекламы long tail here",
                    "address": "a.example", "port": 1}]
    win.lats = {}
    win.render_servers()
    heads = [l for l in win.findChildren(m._ElidedLabel)
             if l.text().startswith("YouTube")]
    assert heads, "stripped head present (no [RU2] prefix)"
    assert all(h.wordWrap() is False for h in heads)
    assert all("…" not in h.text() for h in heads), "elide owns overflow, not data"


def test_ping_paints_in_place(monkeypatch):
    m = app()
    win = _make_win(m, monkeypatch)
    win.servers = [{"remarks": "[PL] t", "address": "a.example", "port": 1},
                   {"remarks": "[DE] t", "address": "b.example", "port": 1}]
    win.lats = {}
    win.render_servers()
    n = win.srv_grid.count()
    assert n == 2
    win._on_ping_result(0, 42)
    assert "42" in win._srv_lat[0].text()
    assert win.srv_grid.count() == n, "no rebuild on ping result"


def test_action_hook_shows_window(monkeypatch, tmp_path):
    import json as _json
    m = app()
    monkeypatch.setattr(m, "STATE_DIR", str(tmp_path))
    monkeypatch.setattr(m, "ACTION_HOOK", str(tmp_path / "gui-action.json"))
    win = _make_win(m, monkeypatch)
    calls = []
    win._tray_show = lambda: calls.append(1)
    (tmp_path / "gui-action.json").write_text(_json.dumps({"action": "show"}))
    win.tick()
    assert calls == [1]
    assert not (tmp_path / "gui-action.json").exists()
    win.tick()
    assert calls == [1], "hook consumed once"


def test_action_hook_navigate(monkeypatch, tmp_path):
    import json as _json
    m = app()
    monkeypatch.setattr(m, "STATE_DIR", str(tmp_path))
    monkeypatch.setattr(m, "ACTION_HOOK", str(tmp_path / "gui-action.json"))
    win = _make_win(m, monkeypatch)
    (tmp_path / "gui-action.json").write_text(
        _json.dumps({"action": "navigate", "page": "traffic"}))
    win.tick()
    assert win.stack.currentWidget() is win.pages["traffic"]


def test_action_hook_scroll(monkeypatch, tmp_path):
    import json as _json
    m = app()
    monkeypatch.setattr(m, "STATE_DIR", str(tmp_path))
    monkeypatch.setattr(m, "ACTION_HOOK", str(tmp_path / "gui-action.json"))
    win = _make_win(m, monkeypatch)
    (tmp_path / "gui-action.json").write_text(
        _json.dumps({"action": "scroll", "by": 200}))
    win.tick()
    assert not (tmp_path / "gui-action.json").exists(), "hook consumed"


def test_refresh_disables_buttons_until_done(monkeypatch):
    m = app()
    win = _make_win(m, monkeypatch)
    win.refresh_sub()
    assert win.sub_updated.text() == "Refreshing…"
    assert all(not b.isEnabled() for b in win._refresh_btns)
    assert any("3373F7" in b.styleSheet() for b in win._refresh_btns)
    rest_key = win.sub_refresh_btn.icon().cacheKey()
    a0 = win._spin_angle
    win._spin_tick()
    assert win._spin_angle != a0, "arrow rotates"
    win._sub_loaded_full("")
    for _ in range(30):
        if getattr(win, "_spin_timer", None) is None:
            break
        win._spin_tick()
    assert getattr(win, "_spin_timer", None) is None, "settled home"
    assert win._spin_angle % 360 == 0
    assert win.sub_refresh_btn.icon().cacheKey() == rest_key, "rest icon back"
    assert all(b.isEnabled() for b in win._refresh_btns)
    assert all(b.styleSheet() == "" for b in win._refresh_btns)
    assert win.sub_updated.text() != "Refreshing…"
    win.refresh_sub()
    win._sub_failed("boom")
    for _ in range(30):
        if getattr(win, "_spin_timer", None) is None:
            break
        win._spin_tick()
    assert all(b.isEnabled() for b in win._refresh_btns)


def test_spin_settles_home_from_any_angle(monkeypatch):
    m = app()
    win = _make_win(m, monkeypatch)
    win.refresh_sub()
    win._spin_angle = 105
    win._spin_stop()
    n = 0
    while getattr(win, "_spin_timer", None) is not None and n < 30:
        win._spin_tick()
        n += 1
    assert getattr(win, "_spin_timer", None) is None
    assert n <= 24, n


def test_spin_hires_base(monkeypatch):
    m = app()
    win = _make_win(m, monkeypatch)
    win.refresh_sub()
    assert win._spin_base.width() >= 48, "hires base kills shimmer"


def test_ping_glow(monkeypatch):
    m = app()
    win = _make_win(m, monkeypatch)
    win._ping_glow(True)
    assert "3373F7" in win.sub_ping_btn.styleSheet()
    win._ping_glow(False)
    assert win.sub_ping_btn.styleSheet() == ""


def test_spin_pixel_proof(monkeypatch, qtbot, tmp_path):
    m = app()
    win = _make_win(m, monkeypatch)
    win.refresh_sub()
    qtbot.wait(350)
    out = str(tmp_path / "spin.png")
    assert win.sub_refresh_btn.grab().save(out), "grab failed"
    print("SPIN-PNG:" + out)


def test_no_dead_autostart_checkbox(monkeypatch):
    m = app()
    win = _make_win(m, monkeypatch)
    texts = [l.text() for l in win.findChildren(m.QLabel)]
    assert not any("Запускать при старте" in t for t in texts)
    assert any("system service" in t for t in texts)


def test_traffic_cards_render(monkeypatch, tmp_path):
    m = app()
    win = _make_win(m, monkeypatch)
    win.navigate("traffic")
    out = str(tmp_path / "traffic.png")
    assert win.pages["traffic"].grab().save(out), "grab failed"
    print("TRAFFIC-PNG:" + out)


def test_server_select_never_connects(monkeypatch):
    m = app()
    win = _make_win(m, monkeypatch)
    seen = {}

    class RecWorker(QObject):
        done = Signal(bool, str)
        phase = Signal(str)

        def __init__(self, idx, start_after=False, mode="smart"):
            super().__init__()
            seen.update(idx=idx, start_after=start_after, mode=mode)

        def start(self):
            pass

    monkeypatch.setattr(m, "SelectWorker", RecWorker)
    win.state = "OFF"
    win._op_in_progress = False
    win._start_server_worker(0)
    assert seen.get("start_after") is False, seen


def test_save_sub_url_roundtrip(monkeypatch, tmp_path):
    m = app()
    p = str(tmp_path / "neodon-sub.py")
    assert m.save_sub_url("https://example.com/sub", p) == ""
    monkeypatch.setattr(m, "CONVERTER", p)
    url, _, _ = m.converter_consts()
    assert url == "https://example.com/sub"
    assert m.save_sub_url("https://other.example/x", p) == ""
    assert m.converter_consts()[0] == "https://other.example/x"
    assert m.save_sub_url("ftp://x", p) != ""
    assert m.save_sub_url("", p) != ""


def test_clamp_to_screen(monkeypatch):
    m = app()
    win = _make_win(m, monkeypatch)
    scr = win.screen() or m.QApplication.primaryScreen()
    avail = scr.availableGeometry()
    win.setGeometry(avail.x() + 4000, avail.y() + 4000,
                    avail.width() + 2000, avail.height() + 2000)
    win._clamp_to_screen()
    g = win.frameGeometry()
    assert g.width() <= avail.width() and g.height() <= avail.height()
    assert g.x() >= avail.x() and g.y() >= avail.y()
    assert g.x() + g.width() <= avail.x() + avail.width()
    assert g.y() + g.height() <= avail.y() + avail.height()


def test_tray_off_restores_default_icon(monkeypatch):
    m = app()
    win = _make_win(m, monkeypatch)
    calls = []

    class FakeTray:
        def setIcon(self, icon):
            calls.append(icon)

        def setToolTip(self, t):
            pass

    win.tray = FakeTray()
    win.status = {"server_tag": "[PL] X"}
    win.mode = "smart"
    win._sync_tray("CONNECTED")
    n1 = len(calls)
    win._sync_tray("OFF")
    assert len(calls) > n1, "OFF must reset the tray icon (flag stuck otherwise)"
