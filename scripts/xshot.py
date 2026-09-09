#!/usr/bin/env python3
"""One-shot: screenshot X display :0 via PIL (game mode verify)."""
import os
import sys

os.environ["DISPLAY"] = sys.argv[1] if len(sys.argv) > 1 else ":0"
from PIL import ImageGrab

im = ImageGrab.grab()
im.save("/home/m26/x11shot.png")
print("XSHOT-OK", im.size)
