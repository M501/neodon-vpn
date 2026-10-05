"""Locate the Neodon GUI window inside a full-screen screenshot by its own palette."""
from PIL import Image

im = Image.open("/home/m26/desk.png").convert("RGB")
w, h = im.size
px = im.load()

PALETTE = {(15, 15, 19), (23, 23, 28), (28, 28, 34), (16, 16, 20), (20, 20, 24)}


def close(c, pal=PALETTE, tol=3):
    return any(abs(c[0] - p[0]) <= tol and abs(c[1] - p[1]) <= tol and abs(c[2] - p[2]) <= tol for p in pal)


col_hits = [0] * w
row_hits = [0] * h
for y in range(0, h, 2):
    for x in range(0, w, 2):
        if close(px[x, y]):
            col_hits[x] += 1
            row_hits[y] += 1

xs = [x for x in range(w) if col_hits[x] > h * 0.10]
ys = [y for y in range(h) if row_hits[y] > w * 0.10]
print("image", (w, h))
if xs and ys:
    print("bbox", min(xs), min(ys), max(xs), max(ys), "size", max(xs) - min(xs), max(ys) - min(ys))
else:
    print("not found")
