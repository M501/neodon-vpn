#!/usr/bin/env python3
"""One-shot: render cropped ru-bez-vpn icon 28px to /tmp/icon28.png."""
import importlib.util
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtWidgets import QApplication

app = QApplication.instance() or QApplication([])
spec = importlib.util.spec_from_file_location(
    "nv", "/tmp/neodon-vpn-test.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
px = m.card_pixmap(os.path.expanduser("~/AI/neodon-vpn/icons/ru-bez-vpn.jpg"))
assert px is not None and px.width() == 28 and px.height() == 28
px.save("/tmp/icon28.png")
print("ICON28-OK", px.width(), px.height())
