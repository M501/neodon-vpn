#!/usr/bin/env python3
"""One-shot: which home-scroll child forces width (spec 023 diag)."""
import importlib.util
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtWidgets import QApplication

app = QApplication.instance() or QApplication([])
spec = importlib.util.spec_from_file_location("nv", "/tmp/neodon-vpn-test.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
w = m.MainWindow()
w.resize(720, 700)
w.show()
app.processEvents()
areas = w.findChildren(m.QScrollArea)
print("SCROLLAREAS:", len(areas))
for a in areas:
    vp = a.viewport().width()
    hb = a.horizontalScrollBar()
    print("VP", vp, "HMAX", hb.maximum(), "HVAL", hb.value())
    inner = a.widget()
    if inner is not None:
        print("CONTENT minW", inner.minimumSizeHint().width())
        lay = inner.layout()
        for i in range(lay.count()):
            it = lay.itemAt(i)
            wd = it.widget()
            if wd is not None:
                print("  child", type(wd).__name__, "minW", wd.minimumSizeHint().width(),
                      repr((wd.text() or "")[:40]))
