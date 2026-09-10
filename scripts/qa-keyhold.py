#!/usr/bin/env python3
"""qa-keyhold.py: persistent uinput keyboard, presses F12 every 2s for 20s."""
import ctypes
import fcntl
import os
import struct
import time

UI_SET_EVBIT = 0x40045564
UI_SET_KEYBIT = 0x40045565
UI_DEV_SETUP = 0x405C5503
UI_DEV_CREATE = 0x5501
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


fd = os.open("/dev/uinput", os.O_WRONLY | os.O_NONBLOCK)
fcntl.ioctl(fd, UI_SET_EVBIT, EV_KEY)
for k in (KEY_F12, 87, 63):
    fcntl.ioctl(fd, UI_SET_KEYBIT, k)
st = UinputSetup()
st.id_bustype = BUS_USB
st.name = b"neodon-qa-keyhold"
fcntl.ioctl(fd, UI_DEV_SETUP, st)
fcntl.ioctl(fd, UI_DEV_CREATE)
print("CREATED", flush=True)
time.sleep(1.0)


def ev(t, c, v):
    os.write(fd, struct.pack("llHHi", 0, 0, t, c, v))


for i in range(6):
    ev(EV_KEY, KEY_F12, 1)
    ev(EV_SYN, 0, 0)
    time.sleep(0.2)
    ev(EV_KEY, KEY_F12, 0)
    ev(EV_SYN, 0, 0)
    print("PRESS", i, flush=True)
    time.sleep(2)
print("HOLD-DONE", flush=True)
time.sleep(30)
