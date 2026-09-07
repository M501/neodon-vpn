#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pure-stdlib v2ray GeoSiteList (dlc.dat) parser. No protobuf dep.
Usage: parse_geosite.py /tmp/dlc.dat [list|dump <tag> ...]
- list: print all country_code tags with domain counts
- dump: print JSON {tag: [values]} for requested tags (type+value, attrs ignored)
"""
import json
import sys


def read_varint(buf, pos):
    shift = 0
    result = 0
    while True:
        b = buf[pos]
        pos += 1
        result |= (b & 0x7F) << shift
        if not (b & 0x80):
            return result, pos
        shift += 7


def parse_fields(buf):
    """Parse protobuf message body -> list of (field_no, wire_type, value)."""
    pos = 0
    end = len(buf)
    out = []
    while pos < end:
        key, pos = read_varint(buf, pos)
        field_no = key >> 3
        wire = key & 7
        if wire == 0:
            val, pos = read_varint(buf, pos)
            out.append((field_no, wire, val))
        elif wire == 2:
            ln, pos = read_varint(buf, pos)
            out.append((field_no, wire, bytes(buf[pos:pos + ln])))
            pos += ln
        elif wire == 5:
            out.append((field_no, wire, bytes(buf[pos:pos + 4])))
            pos += 4
        elif wire == 1:
            out.append((field_no, wire, bytes(buf[pos:pos + 8])))
            pos += 8
        else:
            raise ValueError("bad wire %d" % wire)
    return out


TYPES = {0: "plain", 1: "regex", 2: "domain", 3: "full"}


def load(path):
    raw = open(path, "rb").read()
    sites = {}
    for fno, wire, val in parse_fields(raw):
        if fno == 1 and wire == 2:  # entry: GeoSite
            code = None
            doms = []
            for sfno, swire, sval in parse_fields(val):
                if sfno == 1 and swire == 2:
                    code = sval.decode("utf-8", "replace").lower()
                elif sfno == 2 and swire == 2:
                    dtype = "domain"
                    dval = None
                    for dfno, dwire, dval2 in parse_fields(sval):
                        if dfno == 1 and dwire == 0:
                            dtype = TYPES.get(dval2, "domain")
                        elif dfno == 2 and dwire == 2:
                            dval = dval2.decode("utf-8", "replace")
                    if dval:
                        doms.append((dtype, dval))
            if code:
                sites.setdefault(code, []).extend(doms)
    return sites


def main():
    if len(sys.argv) < 3:
        print("usage: parse_geosite.py <dlc.dat> list|dump [tags...]")
        raise SystemExit(2)
    sites = load(sys.argv[1])
    if sys.argv[2] == "list":
        for tag in sorted(sites):
            print("%s (%d)" % (tag, len(sites[tag])))
        print("TOTAL-TAGS %d" % len(sites))
    elif sys.argv[2] == "dump":
        want = [t.lower() for t in sys.argv[3:]]
        res = {}
        for t in want:
            res[t] = [{"t": dt, "v": dv} for dt, dv in sites.get(t, [])]
        print(json.dumps(res, ensure_ascii=False))
    else:
        raise SystemExit("bad cmd")


if __name__ == "__main__":
    main()
