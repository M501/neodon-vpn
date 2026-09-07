#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""qa-touch.py — real multitouch synthesis via kernel uinput (stdlib only).
On-demand QA hands for Bazzite touchscreen: tap(x,y), swipe(x1,y1,x2,y2,ms).
No daemons, no residue (UI_DEV_DESTROY at exit). Needs write access to
/dev/uinput (tmpfs; one-time `sudo chmod 666 /dev/uinput`, resets on reboot).
Usage: qa-touch.py tap X Y | swipe X1 Y1 X2 Y2 MS
Coordinates: 1080p absolute (INPUT_PROP_DIRECT 1:1 mapping).
"""
import ctypes
import fcntl
import os
import struct
import sys
import time

# Hard ioctl numbers, x86_64 (linux/input.h + linux/uinput.h):
# UI_DEV_CREATE 0x5501, UI_DEV_DESTROY 0x5502,
# UI_DEV_SETUP _IOW('U',3,uinput_setup 1116B) = 0x445C5503,
# UI_SET_{EV,KEY,ABSBIT,PROPBIT} _IOW('U',100/101/103/110,int).
UI_DEV_SETUP = 0x445C5503
UI_DEV_CREATE = 0x5501
UI_DEV_DESTROY = 0x5502
UI_SET_EVBIT = 0x40045564
UI_SET_KEYBIT = 0x40045565
UI_SET_ABSBIT = 0x40045567
UI_SET_PROPBIT = 0x4004556E

EV_SYN, EV_KEY, EV_ABS = 0, 1, 3
SYN_REPORT = 0
BTN_TOUCH = 0x14A
ABS_MT_SLOT, ABS_MT_TRACKING_ID = 0x2F, 0x39
ABS_MT_POSITION_X, ABS_MT_POSITION_Y = 0x35, 0x36
ABS_MT_PRESSURE = 0x3A
INPUT_PROP_DIRECT = 1
BUS_USB = 3


class UinputSetup(ctypes.Structure):
    # kernel order: id, name[80], ff_effects_max, absmax/min/fuzz/flat[64]
    _fields_ = [("id_bustype", ctypes.c_ushort),
                ("id_vendor", ctypes.c_ushort),
                ("id_product", ctypes.c_ushort),
                ("id_version", ctypes.c_ushort),
                ("name", ctypes.c_char * 80),
                ("ff_effects_max", ctypes.c_uint),
                ("absmax", ctypes.c_int * 64),
                ("absmin", ctypes.c_int * 64),
                ("absfuzz", ctypes.c_int * 64),
                ("absflat", ctypes.c_int * 64)]


assert ctypes.sizeof(UinputSetup) == 1116, ctypes.sizeof(UinputSetup)


class UinputUserDev(ctypes.Structure):
    # legacy write path order: name[80], id, ff_effects_max, abs[4][64]
    _fields_ = [("name", ctypes.c_char * 80),
                ("id_bustype", ctypes.c_ushort),
                ("id_vendor", ctypes.c_ushort),
                ("id_product", ctypes.c_ushort),
                ("id_version", ctypes.c_ushort),
                ("ff_effects_max", ctypes.c_uint),
                ("absmax", ctypes.c_int * 64),
                ("absmin", ctypes.c_int * 64),
                ("absfuzz", ctypes.c_int * 64),
                ("absflat", ctypes.c_int * 64)]


def _fill(st, is_setup):
    st.id_bustype = BUS_USB
    st.name = b"neodon-qa-touch"
    st.absmax[ABS_MT_SLOT] = 9
    st.absmax[ABS_MT_TRACKING_ID] = 65535
    st.absmax[ABS_MT_POSITION_X] = 1919
    st.absmax[ABS_MT_POSITION_Y] = 1079
    st.absmax[ABS_MT_PRESSURE] = 255
    return st


def _io(fd, req, arg):
    fcntl.ioctl(fd, req, arg)


def create():
    fd = os.open("/dev/uinput", os.O_WRONLY | os.O_NONBLOCK)
    for b in (EV_SYN, EV_KEY, EV_ABS):
        _io(fd, UI_SET_EVBIT, b)
    _io(fd, UI_SET_KEYBIT, BTN_TOUCH)
    for b in (ABS_MT_SLOT, ABS_MT_TRACKING_ID, ABS_MT_POSITION_X,
              ABS_MT_POSITION_Y, ABS_MT_PRESSURE):
        _io(fd, UI_SET_ABSBIT, b)
    _io(fd, UI_SET_PROPBIT, INPUT_PROP_DIRECT)
    st = _fill(UinputSetup(), True)
    try:
        fcntl.ioctl(fd, UI_DEV_SETUP, st)
    except OSError:
        # legacy path: write uinput_user_dev (name-first layout) instead
        os.write(fd, bytes(_fill(UinputUserDev(), False)))
    fcntl.ioctl(fd, UI_DEV_CREATE)
    time.sleep(1.0)
    _set_resolution()
    return fd


class InputAbsinfo(ctypes.Structure):
    _fields_ = [("value", ctypes.c_int), ("minimum", ctypes.c_int),
                ("maximum", ctypes.c_int), ("fuzz", ctypes.c_int),
                ("flat", ctypes.c_int), ("resolution", ctypes.c_int)]


def _set_resolution():
    # tell libinput our axis density (panel ~160x90mm like the built-in
    # NVTK touchscreen) so touches map 1:1 onto the 1920x1080 output
    node = None
    for ev in os.listdir("/sys/class/input"):
        if not ev.startswith("event"):
            continue
        try:
            with open("/sys/class/input/%s/device/name" % ev) as f:
                if f.read().strip() == "neodon-qa-touch":
                    node = "/dev/input/" + ev
                    break
        except OSError:
            continue
    if node is None:
        return
    try:
        nfd = os.open(node, os.O_RDWR)
    except OSError:
        return
    try:
        for axis, mx in ((ABS_MT_POSITION_X, 1919),
                         (ABS_MT_POSITION_Y, 1079)):
            req = 0x40000000 | (24 << 16) | (0x45 << 8) | (0x40 + axis)
            buf = InputAbsinfo(0, 0, mx, 0, 0, 12)
            fcntl.ioctl(nfd, req, buf)
    except OSError:
        pass
    finally:
        os.close(nfd)


def emit(fd, typ, code, val):
    # struct input_event: long,long + ushort,ushort,int = 24 bytes (64-bit)
    os.write(fd, struct.pack("llHHi", 0, 0, typ, code, val))


def sync(fd):
    emit(fd, EV_SYN, SYN_REPORT, 0)


def down(fd, x, y, tid=45):
    emit(fd, EV_ABS, ABS_MT_SLOT, 0)
    emit(fd, EV_ABS, ABS_MT_TRACKING_ID, tid)
    emit(fd, EV_ABS, ABS_MT_POSITION_X, x)
    emit(fd, EV_ABS, ABS_MT_POSITION_Y, y)
    emit(fd, EV_ABS, ABS_MT_PRESSURE, 50)
    emit(fd, EV_KEY, BTN_TOUCH, 1)
    sync(fd)


def move(fd, x, y):
    emit(fd, EV_ABS, ABS_MT_POSITION_X, x)
    emit(fd, EV_ABS, ABS_MT_POSITION_Y, y)
    sync(fd)


def up(fd):
    emit(fd, EV_ABS, ABS_MT_TRACKING_ID, -1)
    emit(fd, EV_KEY, BTN_TOUCH, 0)
    sync(fd)


def main():
    cmd = sys.argv[1]
    fd = create()
    try:
        if cmd == "tap":
            _, x, y = sys.argv[0], int(sys.argv[2]), int(sys.argv[3])
            down(fd, x, y)
            time.sleep(0.08)
            up(fd)
            print("TAP-OK %d %d" % (x, y))
        elif cmd == "swipe":
            x1, y1, x2, y2, ms = (int(a) for a in sys.argv[2:7])
            steps = max(2, ms // 16)
            down(fd, x1, y1)
            for i in range(1, steps + 1):
                move(fd, x1 + (x2 - x1) * i // steps,
                     y1 + (y2 - y1) * i // steps)
                time.sleep(ms / 1000.0 / steps)
            up(fd)
            print("SWIPE-OK")
        elif cmd == "hold":
            time.sleep(int(sys.argv[2]) if len(sys.argv) > 2 else 10)
            print("HOLD-DONE")
        elif cmd == "taphold":
            # one device: settle, tap, linger (udev/logind/libinput need ~2s
            # to attach a fresh node; separate tap process races and drops)
            x, y = int(sys.argv[2]), int(sys.argv[3])
            time.sleep(3)
            down(fd, x, y)
            time.sleep(0.08)
            up(fd)
            print("TAPHOLD-OK %d %d" % (x, y))
            time.sleep(2)
        else:
            raise SystemExit("usage: tap X Y | swipe X1 Y1 X2 Y2 MS")
    finally:
        try:
            fcntl.ioctl(fd, UI_DEV_DESTROY)
        except OSError:
            pass
        os.close(fd)


if __name__ == "__main__":
    main()
