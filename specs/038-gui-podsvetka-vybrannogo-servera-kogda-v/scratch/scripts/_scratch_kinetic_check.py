"""Verify the shipped _enable_kinetic helper step by step and dump resulting metrics."""
import os
import traceback

os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PySide6.QtWidgets import (QApplication, QLabel, QScrollArea, QScroller,
                               QScrollerProperties, QVBoxLayout, QWidget)

SP = QScrollerProperties.ScrollMetric
OP = QScrollerProperties.OvershootPolicy

app = QApplication([])
sa = QScrollArea()
sa.setWidgetResizable(True)
cont = QWidget()
lay = QVBoxLayout(cont)
for i in range(60):
    lay.addWidget(QLabel("row %d" % i))
sa.setWidget(cont)
sa.resize(400, 300)
sa.show()
app.processEvents()

print("handleInput exposed:", hasattr(QScroller, "handleInput"))

steps = [
    ("grabGesture", lambda: QScroller.grabGesture(sa.viewport(), QScroller.ScrollerGestureType.TouchGesture)),
    ("MousePressEventDelay", lambda: sp.setScrollMetric(SP.MousePressEventDelay, 0.06)),
    ("DragStartDistance", lambda: sp.setScrollMetric(SP.DragStartDistance, 0.012)),
    ("VerticalOvershootPolicy", lambda: sp.setScrollMetric(SP.VerticalOvershootPolicy, OP.OvershootAlwaysOff)),
    ("HorizontalOvershootPolicy", lambda: sp.setScrollMetric(SP.HorizontalOvershootPolicy, OP.OvershootAlwaysOff)),
]
sp = None
for name, fn in steps:
    try:
        if name == "grabGesture":
            fn()
        else:
            if sp is None:
                sp = QScroller.scroller(sa.viewport()).scrollerProperties()
            fn()
        print("STEP OK  ", name)
    except Exception as exc:
        print("STEP FAIL", name, type(exc).__name__, exc)

sp = QScroller.scroller(sa.viewport()).scrollerProperties()
for nm, m in (("MousePressEventDelay", SP.MousePressEventDelay),
              ("DragStartDistance", SP.DragStartDistance),
              ("VerticalOvershootPolicy", SP.VerticalOvershootPolicy),
              ("HorizontalOvershootPolicy", SP.HorizontalOvershootPolicy),
              ("AxisLockThreshold", SP.AxisLockThreshold)):
    print("metric %-26s = %r" % (nm, sp.scrollMetric(m)))
print("overshoot enum: alwaysoff=%r whenscrollable=%r" % (OP.OvershootAlwaysOff, OP.OvershootWhenScrollable))

# does the scroller pan horizontally at all? (synthetic input through the public API)
hb = sa.horizontalScrollBar()
print("hbar range", hb.minimum(), hb.maximum())
if hasattr(QScroller, "handleInput"):
    sc = QScroller.scroller(sa.viewport())
    sc.handleInput(QScroller.Input.InputPress, sa.viewport().rect().center())
    for dx in range(0, 120, 12):
        sc.handleInput(QScroller.Input.InputMove, sa.viewport().rect().center() + __import__("PySide6").QtCore.QPoint(0, 0))
    sc.handleInput(QScroller.Input.InputRelease, sa.viewport().rect().center())
    print("after synthetic move: hbar=", hb.value(), "vbar=", sa.verticalScrollBar().value())
print("DONE")
