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
