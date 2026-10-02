#!/usr/bin/env python3
"""Компактный UI-пасс для neodon-vpn.py (7" 1080p @ scale 2.1, логический холст 914x514).

Каждая замена обязана найтись ровно один раз (иначе abort, файл не трогаем).
Пишем с newline='' — не трогаем переводы строк.
"""
import sys

P = r"C:/AI/Hermes_PROJECTS/neodon-vpn/tests/app/neodon-vpn.py"

EDITS = [
    # ---- QSS ----
    ("QWidget { color: #F5F5F7; font-size: 13px; }",
     "QWidget { color: #F5F5F7; font-size: 12px; }"),
    ("#title { font-size: 12px;", "#title { font-size: 11px;"),
    ("#h1 { font-size: 15px;", "#h1 { font-size: 14px;"),
    ("#h2 { font-size: 13px;", "#h2 { font-size: 12px;"),
    ("#timer { font-size: 24px;", "#timer { font-size: 20px;"),
    ("QPushButton { border: none; border-radius: 10px; padding: 8px 14px;",
     "QPushButton { border: none; border-radius: 10px; padding: 6px 12px;"),
    ("#powerBtn { border-radius: 32px;", "#powerBtn { border-radius: 26px;"),
    ("#modeOn { background: #3373F7; color: #FFFFFF; min-height: 34px; font-size: 13px;",
     "#modeOn { background: #3373F7; color: #FFFFFF; min-height: 28px; font-size: 12px;"),
    ("#modeOff { background: #1F1F26; color: #9B9BA5; min-height: 34px; font-size: 13px;",
     "#modeOff { background: #1F1F26; color: #9B9BA5; min-height: 28px; font-size: 12px;"),
    ("#statusPill { border-radius: 14px; padding: 4px 12px; font-weight: 700; font-size: 13px; }",
     "#statusPill { border-radius: 12px; padding: 3px 10px; font-weight: 700; font-size: 12px; }"),
    ("#badge { background: #1F1F26; border: 1px solid #33333D; border-radius: 14px; color: #3373F7; font-size: 13px;",
     "#badge { background: #1F1F26; border: 1px solid #33333D; border-radius: 12px; color: #3373F7; font-size: 12px;"),
    ("#hint { color: #6B6B76; font-size: 12px; }",
     "#hint { color: #6B6B76; font-size: 11px; }"),
    ("QProgressBar { background: #1F1F26; border: none; border-radius: 5px; min-height: 10px; max-height: 10px;",
     "QProgressBar { background: #1F1F26; border: none; border-radius: 4px; min-height: 8px; max-height: 8px;"),
    ("QScrollBar:vertical { background: transparent; width: 8px; }",
     "QScrollBar:vertical { background: transparent; width: 6px; }"),
    ("QComboBox { background: #1F1F26; border: 1px solid #33333D; border-radius: 10px; padding: 7px 12px; }",
     "QComboBox { background: #1F1F26; border: 1px solid #33333D; border-radius: 10px; padding: 5px 10px; }"),
    ("QLineEdit { background: #1F1F26; border: 1px solid #33333D; border-radius: 10px; padding: 8px 12px; }",
     "QLineEdit { background: #1F1F26; border: 1px solid #33333D; border-radius: 10px; padding: 6px 10px; }"),
    ("QCheckBox::indicator { width: 18px; height: 18px;",
     "QCheckBox::indicator { width: 16px; height: 16px;"),
    ("monospace; font-size: 11px; }", "monospace; font-size: 10px; }"),
    # ---- widgets / размеры ----
    ("        self.setFixedSize(46, 46)\n", "        self.setFixedSize(38, 38)\n"),
    ("    def __init__(self, icon_name, size=22, color=", "    def __init__(self, icon_name, size=18, color="),
    ("        _w, _h = 700, 660", "        _w, _h = 820, 620"),
    ("        self.setMinimumSize(420, 440)", "        self.setMinimumSize(420, 380)"),
    ("        side.setFixedWidth(58)", "        side.setFixedWidth(46)"),
    ("        sl.setContentsMargins(6, 10, 6, 10)", "        sl.setContentsMargins(4, 8, 4, 8)"),
    ("        self.power.setFixedSize(64, 64)", "        self.power.setFixedSize(54, 54)"),
    ("        self.power.setIconSize(QSize(26, 26))", "        self.power.setIconSize(QSize(22, 22))"),
    ("        hdr.setContentsMargins(14, 12, 14, 4)", "        hdr.setContentsMargins(12, 8, 12, 2)"),
    ("            bl.setContentsMargins(8, 3, 8, 8)\n            bl.setSpacing(6)",
     "            bl.setContentsMargins(8, 2, 8, 6)\n            bl.setSpacing(5)"),
    ("        bl.setContentsMargins(8, 3, 8, 8)\n        bl.setSpacing(6)",
     "        bl.setContentsMargins(8, 2, 8, 6)\n        bl.setSpacing(5)"),
    ("        lay.setContentsMargins(12, 8, 12, 10)\n        lay.setSpacing(6)",
     "        lay.setContentsMargins(10, 6, 10, 8)\n        lay.setSpacing(5)"),
    ("        hl.setContentsMargins(12, 12, 12, 12)\n        hl.setSpacing(10)",
     "        hl.setContentsMargins(10, 8, 10, 8)\n        hl.setSpacing(8)"),
    ("        ic.setPixmap(icon_pixmap(icon, 20, \"#3373F7\"))",
     "        ic.setPixmap(icon_pixmap(icon, 18, \"#3373F7\"))"),
    ("            hl.setContentsMargins(12, 10, 12, 10)\n            hl.setSpacing(10)",
     "            hl.setContentsMargins(10, 6, 10, 6)\n            hl.setSpacing(8)"),
    ("            ic.setFixedSize(28, 28)", "            ic.setFixedSize(24, 24)"),
    ("            info_btn.setFixedSize(30, 30)", "            info_btn.setFixedSize(26, 26)"),
    ("            rb.setFixedSize(18, 18)", "            rb.setFixedSize(16, 16)"),
    ("        self.sub_refresh_btn.setFixedSize(30, 30)", "        self.sub_refresh_btn.setFixedSize(26, 26)"),
    ("        self.srv_grid.setSpacing(8)", "        self.srv_grid.setSpacing(6)"),
    ("            hl.setContentsMargins(8, 5, 8, 5)\n            hl.setSpacing(8)",
     "            hl.setContentsMargins(8, 4, 8, 4)\n            hl.setSpacing(6)"),
    ("            fl.setFixedWidth(30)", "            fl.setFixedWidth(26)"),
    ("            lat_lbl.setFixedWidth(64)", "            lat_lbl.setFixedWidth(52)"),
]

with open(P, encoding="utf-8", newline="") as f:
    src = f.read()

fresh = src
fails = []
for old, new in EDITS:
    n = fresh.count(old)
    if n != 1:
        fails.append((n, old[:70]))
        continue
    fresh = fresh.replace(old, new)

if fails:
    print("ABORT — замены не найдены ровно один раз:")
    for n, s in fails:
        print(f"  count={n}: {s}")
    sys.exit(1)

with open(P, "w", encoding="utf-8", newline="") as f:
    f.write(fresh)

print(f"OK: применено {len(EDITS)} замен, файл {len(src)} -> {len(fresh)} байт")
