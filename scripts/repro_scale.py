#!/usr/bin/env python3
"""One-shot: render home+servers at handheld scale (spec 023 diag)."""
import importlib.util
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ["QT_SCALE_FACTOR"] = "2"
from PySide6.QtWidgets import QApplication

app = QApplication.instance() or QApplication([])
spec = importlib.util.spec_from_file_location("nv", "/tmp/neodon-vpn-test.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
w = m.MainWindow()
w.servers = [{"remarks": r, "address": "a%d.example" % i, "port": 1} for i, r in enumerate(
    ["\U0001F1F5\U0001F1F1 [PL] NEODON VPN 5366990698",
     "\U0001F1F7\U0001F1FA [RU] YouTube без рекламы",
     "\U0001F1FA\U0001F1F8 [US] NEODON VPN Slow here yes indeed",
     "\U0001F1EE\U0001F1F8 [IS] Gemini, YouTube"])]
w.lats = {}
w.resize(720, 700)
w.show()
w.render_servers()
app.processEvents()
areas = w.findChildren(m.QScrollArea)
for a in areas:
    hb = a.horizontalScrollBar()
    if hb.maximum() > 0:
        print("OVERFLOW area VP", a.viewport().width(), "HMAX", hb.maximum())
w.stack.currentWidget()
w.grab().save("/tmp/scale2x.png")
print("SCALE2X-OK")
