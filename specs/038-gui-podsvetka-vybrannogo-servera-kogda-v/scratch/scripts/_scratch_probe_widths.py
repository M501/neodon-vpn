"""Diagnose: how much horizontal scroll range each GUI page has, and which child forces it.

Pure measurement: builds MainWindow offscreen (the flock lives in main(), so this
never touches the live instance) and prints per-page numbers.
"""
import importlib.util
import json
import os
import sys

os.environ["QT_QPA_PLATFORM"] = "offscreen"
sys.argv = ["neodon-vpn.py"]

from PySide6.QtWidgets import QApplication, QScrollArea, QWidget

app = QApplication([])
spec = importlib.util.spec_from_file_location("ngui", "/home/m26/AI/neodon-vpn/neodon-vpn.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

win = mod.MainWindow()
win.resize(820, 620)
win.show()
for _ in range(3):
    app.processEvents()

out = {"window": [win.width(), win.height()], "pages": []}
for name, page in win.pages.items():
    sa = page.findChild(QScrollArea)
    if sa is None:
        out["pages"].append({"page": name, "scroll": None})
        continue
    cont = sa.widget()
    hb = sa.horizontalScrollBar()
    kids = []
    for c in cont.findChildren(QWidget):
        try:
            mn = c.minimumSizeHint().width()
        except Exception:
            continue
        txt = ""
        try:
            txt = (c.text() or "")[:40]
        except Exception:
            pass
        kids.append((mn, type(c).__name__, c.objectName(), txt))
    kids.sort(reverse=True)
    out["pages"].append({
        "page": name,
        "viewport_w": sa.viewport().width(),
        "content_w": cont.width(),
        "content_minHint_w": cont.minimumSizeHint().width(),
        "hbar_range": [hb.minimum(), hb.maximum()],
        "widest_children": kids[:4],
    })

print(json.dumps(out, ensure_ascii=False, indent=1))
