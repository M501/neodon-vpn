#!/usr/bin/env python3
"""One-shot: compare two files ignoring CR (Windows CRLF vs host LF)."""
import sys

a = open(sys.argv[1], "rb").read().replace(b"\r", b"")
b = open(sys.argv[2], "rb").read().replace(b"\r", b"")
print("CONTENT-IN-SYNC" if a == b else "DIVERGED len %d vs %d" % (len(a), len(b)))
