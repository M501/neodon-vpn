"""Which GUI pages overflow horizontally at the LIVE window size (565x543 logical)?"""
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

for w, h in ((565, 543), (820, 620), (460, 500)):
    win = mod.MainWindow()
    win.resize(w, h)
    win.show()
    for _ in range(3):
        app.processEvents()
    print("=== window %dx%d ===" % (w, h))
    for name, page in win.pages.items():
        sa = page.findChild(QScrollArea)
        if sa is None:
            print("  %-9s (no scroll area)" % name)
            continue
        cont = sa.widget()
        hb = sa.horizontalScrollBar()
        print("  %-9s vp=%3d content=%3d minHint=%3d hrange=%d  widest=%s" % (
            name, sa.viewport().width(), cont.width(), cont.minimumSizeHint().width(),
            hb.maximum(), [c[0] for c in sorted(
                [(c.minimumSizeHint().width(), type(c).__name__) for c in cont.findChildren(QWidget)],
                reverse=True)[:3]]))
    win.deleteLater()
    del win
print("DONE")
