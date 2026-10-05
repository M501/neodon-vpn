"""Find server-card rectangles and the accent-framed (selected) card in a grab.

Cards are QFrame#serverCard rounded rects; the selected one carries a 2px #3373F7
border. Prints the card grid cells (row/col) and which cell holds the accent frame,
plus the accent frame's bbox on the panel.
"""
import sys
from collections import defaultdict

from PIL import Image

im = Image.open(sys.argv[1]).convert("RGB")
W, H = im.size
px = im.load()

ACCENT = (51, 115, 247)      # #3373F7
CARD_BG = (28, 28, 34)       # #1C1C22
SEL_BG = (22, 32, 58)        # #16203A
LIVE_BG = (20, 37, 30)       # #14251E


def near(c, t, tol=10):
    return abs(c[0] - t[0]) <= tol and abs(c[1] - t[1]) <= tol and abs(c[2] - t[2]) <= tol


# 1) accent pixels (selected frame) — restrict to the content area, skip the sidebar
acc = [(x, y) for y in range(0, H, 2) for x in range(0, W, 2)
       if x > W * 0.10 and near(px[x, y], ACCENT)]
print("accent pixels:", len(acc))
if acc:
    xs = [p[0] for p in acc]
    ys = [p[1] for p in acc]
    print("accent cluster bbox:", (min(xs), min(ys), max(xs), max(ys)))

# 2) card bodies by background colour
rows = defaultdict(int)
cells = []
for bg, name in ((CARD_BG, "plain"), (SEL_BG, "selected"), (LIVE_BG, "live")):
    hits = [(x, y) for y in range(0, H, 3) for x in range(0, W, 3)
            if x > W * 0.10 and near(px[x, y], bg, 6)]
    print("%-9s bg pixels: %d" % (name, len(hits)))
    if hits:
        xs = [p[0] for p in hits]
        ys = [p[1] for p in hits]
        cells.append((name, (min(xs), min(ys), max(xs), max(ys))))

for name, box in cells:
    print("bbox", name, box)

# 3) column/row split of the card grid: accent frame tells which cell is selected
if acc:
    ax0, ay0, ax1, ay1 = min(xs), min(ys), max(xs), max(ys)
    # 2-column grid inside the content: column split at the mid of the content area
    mid = (W * 0.10 + W) / 2.0
    col = 0 if (ax0 + ax1) / 2 < mid else 1
    print("selected frame: mid_x=%.0f  centre_x=%.0f -> column %d" % (mid, (ax0 + ax1) / 2, col))
