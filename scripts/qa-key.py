#!/usr/bin/env python3
"""One-shot: press Super+S (gamescope screenshot) via uinput (proven layout)."""
import ctypes
import fcntl
import os
import struct
import time

UI_SET_EVBIT = 0x40045564
UI_SET_KEYBIT = 0x40045565
UI_DEV_SETUP = 0x445C5503
UI_DEV_CREATE = 0x5501
UI_DEV_DESTROY = 0x5502
EV_SYN, EV_KEY = 0, 1
KEY_LEFTMETA, KEY_S = 125, 31


class UinputSetup(ctypes.Structure):
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


assert ctypes.sizeof(UinputSetup) == 1116


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
    fd = os.open("/dev/uinput", os.O_WRONLY | os.O_NONBLOCK)
    fcntl.ioctl(fd, UI_SET_EVBIT, EV_KEY)
    fcntl.ioctl(fd, UI_SET_EVBIT, EV_SYN)
    fcntl.ioctl(fd, UI_SET_KEYBIT, KEY_LEFTMETA)
    fcntl.ioctl(fd, UI_SET_KEYBIT, KEY_S)
    st = UinputSetup()
    st.id_bustype = 3
    st.name = b"neodon-qa-key"
    try:
        fcntl.ioctl(fd, UI_DEV_SETUP, st)
    except OSError:
        legacy = UinputUserDev()
        legacy.id_bustype = 3
        legacy.name = b"neodon-qa-key"
        os.write(fd, bytes(legacy))
    fcntl.ioctl(fd, UI_DEV_CREATE)
    time.sleep(1.0)

    def ev(t, c, v):
        os.write(fd, struct.pack("llHHI", 0, 0, t, c, v))

    ev(EV_KEY, KEY_LEFTMETA, 1)
    ev(EV_SYN, 0, 0)
    time.sleep(0.2)
    ev(EV_KEY, KEY_S, 1)
    ev(EV_SYN, 0, 0)
    time.sleep(0.2)
    ev(EV_KEY, KEY_S, 0)
    ev(EV_SYN, 0, 0)
    time.sleep(0.2)
    ev(EV_KEY, KEY_LEFTMETA, 0)
    ev(EV_SYN, 0, 0)
    time.sleep(0.5)
    fcntl.ioctl(fd, UI_DEV_DESTROY)
    os.close(fd)
    print("KEY-DONE")


main()
