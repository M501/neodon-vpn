#!/usr/bin/env python3
"""qa-key.py: uinput keyboard keypress (game-mode screenshots via F12).

Same device-creation pattern as qa-touch.py (UI_DEV_SETUP, legacy fallback).
Usage: python3 qa-key.py [keycode]  (default 88 = KEY_F12)
"""
import ctypes
import fcntl
import os
import struct
import sys
import time

UI_SET_EVBIT = 0x40045564
UI_SET_KEYBIT = 0x40045565
UI_DEV_SETUP = 0x405C5503
UI_DEV_CREATE = 0x5501
UI_DEV_DESTROY = 0x5502
EV_SYN = 0x00
EV_KEY = 0x01
BUS_USB = 0x03
KEY_F12 = 88


class UinputSetup(ctypes.Structure):
    _fields_ = [("id_bustype", ctypes.c_ushort),
                ("id_vendor", ctypes.c_ushort),
                ("id_product", ctypes.c_ushort),
                ("id_version", ctypes.c_ushort),
                ("name", ctypes.c_char * 80),
                ("ff_effects_max", ctypes.c_uint),
                ("_pad", ctypes.c_uint * 820)]


class UinputUserDev(ctypes.Structure):
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


def main():
    key = int(sys.argv[1]) if len(sys.argv) > 1 else KEY_F12
    fd = os.open("/dev/uinput", os.O_WRONLY | os.O_NONBLOCK)
    try:
        fcntl.ioctl(fd, UI_SET_EVBIT, EV_KEY)
        fcntl.ioctl(fd, UI_SET_KEYBIT, key)
        st = UinputSetup()
        st.id_bustype = BUS_USB
        st.name = b"neodon-qa-key"
        try:
            fcntl.ioctl(fd, UI_DEV_SETUP, st)
        except OSError:
            legacy = UinputUserDev()
            legacy.name = b"neodon-qa-key"
            legacy.id_bustype = BUS_USB
            os.write(fd, bytes(legacy))
        fcntl.ioctl(fd, UI_DEV_CREATE)
        time.sleep(0.8)

        def ev(t, c, v):
            os.write(fd, struct.pack("llHHi", 0, 0, t, c, v))

        ev(EV_KEY, key, 1)
        ev(EV_SYN, 0, 0)
        time.sleep(0.15)
        ev(EV_KEY, key, 0)
        ev(EV_SYN, 0, 0)
        time.sleep(0.5)
        print("KEYPRESS-OK", key, flush=True)
    finally:
        try:
            fcntl.ioctl(fd, UI_DEV_DESTROY)
        except OSError:
            pass
        os.close(fd)


main()
