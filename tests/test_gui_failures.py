#!/usr/bin/env python3
"""Failure-path tests: broken inputs must never kill the app.

A non-technical user cannot repair anything, so every malformed/missing artifact has
to degrade gracefully: no traceback out of MainWindow.__init__, no crash on a bad
status document, no "silent nothing" on a second refresh tap.

Same harness as tests/test_gui_logic.py (stubbed backend, inert CmdWorker).
"""
import json
import os
import sys

if not (os.environ.get("WAYLAND_DISPLAY") or os.environ.get("DISPLAY")):
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

APP = os.environ.get("NEODON_APP", "/home/m26/AI/neodon-vpn/neodon-vpn.py")
_mod = None


def _app():
    global _mod
    if _mod is None:
        if not os.path.exists(APP):
            import pytest
            pytest.skip("GUI source not mounted at %s" % APP)
        import importlib.util
        spec = importlib.util.spec_from_file_location("neodon_vpn_app", APP)
        _mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(_mod)
    return _mod


class _Sig(object):
    def __init__(self):
        self._slots = []

    def connect(self, slot):
        self._slots.append(slot)

    def emit(self, *a):
        for slot in list(self._slots):
            slot(*a)


class _SigPair(object):
    def __init__(self):
        self.ok = _Sig()
        self.fail = _Sig()


class _InertWorker(object):
    def __init__(self, *a, **k):
        s = _SigPair()
        self.ok = s.ok
        self.fail = s.fail

    def start(self):
        pass

    def wait(self, ms=0):
        return True


def _stub(m, monkeypatch):
    monkeypatch.setattr(m, "CmdWorker", _InertWorker)
    monkeypatch.setattr(m, "run_cmd", lambda cmd, timeout=20: (0, "{}", ""))
    monkeypatch.setattr(m, "load_servers", lambda: [])
    return m


def _win(m, monkeypatch):
    from PySide6.QtWidgets import QApplication
    QApplication.instance() or QApplication([])
    w = _stub(m, monkeypatch).MainWindow()
    w._log_transition = lambda *a, **k: None
    w._journal_transition = lambda *a, **k: None
    return w


# --- raw.json (server inventory) ---------------------------------------------
def test_load_servers_survives_every_broken_shape(tmp_path, monkeypatch):
    m = _app()
    bad_shapes = ["{not json", "\"a string\"", "null", "{\"outbounds\": []}", "[1, 2]",
                  "[]", "{\"tag\": \"x\"}"]
    for i, blob in enumerate(bad_shapes):
        p = tmp_path / ("raw%d.json" % i)
        p.write_text(blob)
        monkeypatch.setattr(m, "RAW", str(p))
        out = m.load_servers()
        assert isinstance(out, list), "raw.json=%r must degrade to a list, got %r" % (blob, out)


def test_mainwindow_starts_with_corrupt_state_files(tmp_path, monkeypatch):
    """The window must open even when every state file is garbage."""
    m = _app()
    for name, blob in (("gui-state.json", "{not json"), ("selected-server.json", "[1]"),
                       ("sub-cache.json", "\"nope\""), ("app-rules.json", "{bad"),
                       ("raw.json", "{\"oops\": 1}")):
        (tmp_path / name).write_text(blob)
    monkeypatch.setattr(m, "STATE_DIR", str(tmp_path))
    monkeypatch.setattr(m, "RULES_JSON", str(tmp_path / "app-rules.json"))
    monkeypatch.setattr(m, "RAW", str(tmp_path / "raw.json"))
    monkeypatch.setattr(m, "SELECTED_JSON", str(tmp_path / "selected-server.json"))
    win = _win(m, monkeypatch)          # must not raise
    assert win.servers == []
    assert m.selected_server() == {}


# --- status documents ---------------------------------------------------------
def test_status_loaded_ignores_garbage_and_keeps_ui_alive(monkeypatch):
    m = _app()
    win = _win(m, monkeypatch)
    before = win.state
    for blob in ("", "not json", "[]", "null", "\"str\"", "{\"actual_state\": null}"):
        win._status_loaded(blob)        # must not raise, must not corrupt the state
    assert win.state == before, "a malformed status must not change the visible state"


# --- subscription -------------------------------------------------------------
def test_second_refresh_is_rejected_not_double_run(monkeypatch):
    m = _app()
    win = _win(m, monkeypatch)
    monkeypatch.setattr(win, "_sub_script", lambda fetch_body: ("echo DONE", "https://x"))
    win.refresh_sub()
    assert getattr(win, "_sub_busy", False) is True
    calls = []
    monkeypatch.setattr(win, "_sub_script",
                        lambda fetch_body: calls.append(1) or ("echo DONE", "https://x"))
    win.refresh_sub()                   # second tap while the first is in flight
    assert calls == [], "a second refresh must not start another download"


def test_sub_url_rejects_quote_injection(tmp_path, monkeypatch):
    m = _app()
    target = tmp_path / "neodon-sub.py"
    target.write_text("URL='https://old'\n")
    for bad in ("https://x/'\nimport os;os.system('rm -rf ~')#", "https://x/\\y", "https://x/a\nb"):
        err = m.save_sub_url(bad, str(target))
        assert err, "URL %r must be refused" % bad
        assert target.read_text() == "URL='https://old'\n", "the file must stay untouched"
    assert m.save_sub_url("https://good.example/sub", str(target)) == ""
    assert "good.example" in target.read_text()


# --- ping results -------------------------------------------------------------
def test_stale_ping_result_is_dropped(monkeypatch):
    m = _app()
    win = _win(m, monkeypatch)
    win.servers = [{"remarks": "[PL] t", "address": "a", "port": 1}]
    win.render_servers()
    win.lats = {}
    win._srv_gen = 5
    win._on_ping_result(0, 42, gen=4)   # result of the previous grid
    assert win.lats == {}, "a stale ping must not paint into the new grid"
    win._on_ping_result(0, 42, gen=5)
    assert win.lats.get(0) == 42
