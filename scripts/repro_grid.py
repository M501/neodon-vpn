#!/usr/bin/env python3
"""One-shot: geometry of server grid with REAL remarks (spec 018 diag)."""
import importlib.util
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtWidgets import QApplication

app = QApplication.instance() or QApplication([])
spec = importlib.util.spec_from_file_location("nv", "/tmp/neodon-vpn-test.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
REMARKS = ["\U0001F1F5\U0001F1F1 [PL] NEODON VPN 5366990698",
           "\U0001F1F3\U0001F1F1 [NL] NEODON VPN \U0001F51DTikTok",
           "\U0001F1E6\U0001F1F9 [AT] NEODON VPN",
           "\U0001F1F8\U0001F1EA [SW] NEODON VPN \U0001F51DTikTok",
           "\U0001F1EB\U0001F1EE [FI] YouTube без рекламы",
           "\U0001F1F7\U0001F1FA [RU] YouTube без рекламы",
           "\U0001F1F7\U0001F1FA [RU2] YouTube без рекламы",
           "\U0001F1F7\U0001F1FA [RU3] YouTube без рекламы",
           "\U0001F1FA\U0001F1F8 [US] NEODON VPN\u2716\uFE0FS slow",
           "\U0001F1EE\U0001F1F8 [IS] Gemini, YouTube"]
w = m.MainWindow()
w.servers = [{"remarks": r, "address": "a%d.example" % i, "port": 1}
             for i, r in enumerate(REMARKS)]
w.lats = {}
w.resize(720, 700)
w.show()
w.render_servers()
app.processEvents()
print("WIN", w.width(), "GRID-COLS", w.srv_grid.columnCount())
for i in range(min(4, len(REMARKS))):
    item = w.srv_grid.itemAtPosition(i // 2, i % 2)
    row = item.widget() if item else None
    print(i, "ROW-W", row.width() if row else None,
          "HEAD", repr(m.re.sub(r"^\[[A-Za-z]{2}\]\s*", "", m.strip_flags(REMARKS[i]).strip())[:30]))
area = w.stack.currentWidget().findChild(m.QScrollArea)
print("QScrollArea:", area is not None)
if area is not None:
    print("VP-W", area.viewport().width(), "HBAR", area.horizontalScrollBar().value(),
          area.horizontalScrollBar().maximum(), "VBAR", area.verticalScrollBar().value())
