#!/usr/bin/env python3
"""List Wayland globals on gamescope-0 (does it have screencopy?)."""
import os

os.environ["XDG_RUNTIME_DIR"] = "/run/user/1000"
os.environ["WAYLAND_DISPLAY"] = "gamescope-0"

from pywayland.client import Display

disp = Display()
disp.connect()
reg = disp.get_registry()


def on_global(r, id, iface, ver):
    if "copy" in iface or "screencast" in iface or "output" in iface or iface in (
            "wl_shm", "wl_compositor", "xdg_output_manager_v1"):
        print(id, iface, ver)


reg.dispatcher["global"] = on_global
disp.roundtrip()
print("ROUNDTRIP-OK")
disp.disconnect()
