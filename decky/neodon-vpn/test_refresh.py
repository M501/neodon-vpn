#!/usr/bin/env python3
"""Decky backend tests part 2: userinfo parse + refresh_sub against a local
subscription server (no provider traffic, no RAW mutation of real data —
HOME is redirected to tmp)."""
import asyncio
import importlib.util
import json
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

spec = importlib.util.spec_from_file_location("decky_backend", sys.argv[1])
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

BODY = json.dumps([{"remarks": "t", "outbounds": [
    {"protocol": "vless", "settings": {"vnext": [{"address": "x.example"}]}}]}])
USERINFO = "upload=100; download=200; total=1000; expire=1801345352"


class H(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("subscription-userinfo", USERINFO)
        self.send_header("Content-Length", str(len(BODY)))
        self.end_headers()
        self.wfile.write(BODY.encode())

    def log_message(self, *a):
        pass


async def main():
    fails = []

    def check(name, cond):
        print(("ok  " if cond else "FAIL"), name)
        if not cond:
            fails.append(name)

    p = m.parse_userinfo(USERINFO)
    check("userinfo-parse", p is not None and p["used"] == "0.0 GB / 0.0 GB")
    check("userinfo-none", m.parse_userinfo("garbage") is None)

    import tempfile
    import os
    tmp = tempfile.mkdtemp()
    m.RAW = os.path.join(tmp, "raw.json")
    m.QUOTA = os.path.join(tmp, "sub-cache.json")
    m.CONVERTER = os.path.join(tmp, "neodon-sub.py")
    srv = HTTPServer(("127.0.0.1", 0), H)
    port = srv.server_address[1]
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    with open(m.CONVERTER, "w") as f:
        f.write("URL='http://127.0.0.1:%d/sub'\n" % port)
    r = await m.refresh_sub()
    check("refresh-ok", r.get("ok") is True)
    check("refresh-servers", r.get("servers") == 1)
    check("refresh-quota", isinstance(r.get("quota"), dict))
    check("raw-written", os.path.exists(m.RAW))
    srv.shutdown()
    print("FAILURES:", fails if fails else "none")
    return 1 if fails else 0


sys.exit(asyncio.run(main()))
