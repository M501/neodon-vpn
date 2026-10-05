#!/usr/bin/env python3
"""Synthetic single-finger DRAG via uinput (stdlib ctypes only).

Usage: touch_drag.py X1 Y1 X2 Y2 [STEPS] [STEP_MS] [HOLD_MS]
X/Y in output pixels (1920x1080 panel). One device lifecycle per call.
Adapted from touch_tap.py (same device identity, so udev already knows it).
"""
import ctypes  # noqa: F401  (kept for parity with touch_tap.py)
import fcntl
import os
import struct
import sys
import time

UINPUT = "/dev/uinput"
NAME = b"hermes-test-touch"

EV_SYN, EV_KEY, EV_ABS = 0, 1, 3
BTN_TOUCH = 330
BTN_TOOL_FINGER = 325
ABS_MT_SLOT, ABS_MT_TRACKING_ID = 47, 57
ABS_MT_POSITION_X, ABS_MT_POSITION_Y, ABS_MT_PRESSURE = 53, 54, 58
PROP_DIRECT = 1

UI_SET_EVBIT = 0x40045564
UI_SET_KEYBIT = 0x40045565
UI_SET_ABSBIT = 0x40045567
UI_SET_PROPBIT = 0x4004556E
UI_DEV_CREATE = 0x5501
UI_DEV_DESTROY = 0x5502
UI_ABS_SETUP = (1 << 30) | (28 << 16) | (0x55 << 8) | 4


def uinput_user_dev() -> bytes:
    name = NAME + b"\x00" * (80 - len(NAME))
    dev_id = struct.pack("HHHH", 0x1, 0x1, 0x1, 0x1)
    ff = struct.pack("I", 0)
    amax = [0] * 64
    amin = [0] * 64
    afuzz = [0] * 64
    aflat = [0] * 64
    amax[9] = 9
    amax[ABS_MT_TRACKING_ID] = 65535
    amax[ABS_MT_POSITION_X] = 1919
    amax[ABS_MT_POSITION_Y] = 1079
    amax[ABS_MT_PRESSURE] = 255
    pack = lambda arr: struct.pack("64i", *arr)  # noqa: E731
    return name + dev_id + ff + pack(amax) + pack(amin) + pack(afuzz) + pack(aflat)


def emit(fd: int, t: int, code: int, value: int) -> None:
    os.write(fd, struct.pack("qqHHi", 0, 0, t, code, value))


def main() -> None:
    x1, y1, x2, y2 = (int(v) for v in sys.argv[1:5])
    steps = int(sys.argv[5]) if len(sys.argv) > 5 else 16
    step_ms = int(sys.argv[6]) if len(sys.argv) > 6 else 14
    fd = os.open(UINPUT, os.O_WRONLY | os.O_NONBLOCK)
    try:
        for bit, val in (
            (UI_SET_EVBIT, EV_SYN), (UI_SET_EVBIT, EV_KEY), (UI_SET_EVBIT, EV_ABS),
            (UI_SET_KEYBIT, BTN_TOUCH), (UI_SET_KEYBIT, BTN_TOOL_FINGER),
            (UI_SET_ABSBIT, ABS_MT_SLOT), (UI_SET_ABSBIT, ABS_MT_TRACKING_ID),
            (UI_SET_ABSBIT, ABS_MT_POSITION_X), (UI_SET_ABSBIT, ABS_MT_POSITION_Y),
            (UI_SET_ABSBIT, ABS_MT_PRESSURE), (UI_SET_PROPBIT, PROP_DIRECT),
        ):
            fcntl.ioctl(fd, bit, val)
        os.write(fd, uinput_user_dev())
        for axis, mx in ((ABS_MT_POSITION_X, 1919), (ABS_MT_POSITION_Y, 1079)):
            fcntl.ioctl(fd, UI_ABS_SETUP, struct.pack("HHiiiiii", axis, 0, 0, 0, mx, 0, 0, 12))
        fcntl.ioctl(fd, UI_DEV_CREATE)
        time.sleep(3)  # udev/logind/libinput attach
        emit(fd, EV_ABS, ABS_MT_SLOT, 0)
        emit(fd, EV_ABS, ABS_MT_TRACKING_ID, 42)
        emit(fd, EV_ABS, ABS_MT_POSITION_X, x1)
        emit(fd, EV_ABS, ABS_MT_POSITION_Y, y1)
        emit(fd, EV_ABS, ABS_MT_PRESSURE, 100)
        emit(fd, EV_KEY, BTN_TOOL_FINGER, 1)
        emit(fd, EV_KEY, BTN_TOUCH, 1)
        emit(fd, EV_SYN, 0, 0)
        time.sleep(0.06)
        for i in range(1, steps + 1):
            x = int(round(x1 + (x2 - x1) * i / steps))
            y = int(round(y1 + (y2 - y1) * i / steps))
            emit(fd, EV_ABS, ABS_MT_POSITION_X, x)
            emit(fd, EV_ABS, ABS_MT_POSITION_Y, y)
            emit(fd, EV_SYN, 0, 0)
            time.sleep(step_ms / 1000.0)
        emit(fd, EV_ABS, ABS_MT_TRACKING_ID, -1)
        emit(fd, EV_KEY, BTN_TOOL_FINGER, 0)
        emit(fd, EV_KEY, BTN_TOUCH, 0)
        emit(fd, EV_SYN, 0, 0)
        time.sleep(1.5)
        print("DRAG-OK", x1, y1, "->", x2, y2, "steps", steps)
    finally:
        try:
            fcntl.ioctl(fd, UI_DEV_DESTROY)
        except OSError:
            pass
        os.close(fd)


if __name__ == "__main__":
    main()
