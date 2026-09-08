#!/usr/bin/env python3
"""One-shot: what classes are the YouTube labels?"""
import importlib.util
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtWidgets import QApplication

app = QApplication.instance() or QApplication([])
spec = importlib.util.spec_from_file_location("nv", "/tmp/neodon-vpn-test.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
print("has _ElidedLabel:", hasattr(m, "_ElidedLabel"))
win = m.MainWindow()
win.servers = [{"remarks": "[RU2] YouTube X", "address": "a", "port": 1}]
win.lats = {}
win.render_servers()
for w in win.findChildren(m.QLabel):
    t = w.text()
    if t.startswith("YouTube") or "YouTube" in t:
        print(type(w).__name__, isinstance(w, m._ElidedLabel), repr(t[:40]))
