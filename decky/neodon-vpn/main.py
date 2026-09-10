#!/usr/bin/env python3
"""Neodon VPN Decky backend: thin wrappers, zero routing logic.

Mutations are explicit argv from a hardcoded allowlist (no shell=True,
no string interpolation, server idx validated). Reads only JSON files.
No root flag needed: everything runs as the user, like the Desktop GUI.
"""
import asyncio
import datetime
import http.cookiejar
import json
import os
import re
import urllib.request

try:
    import decky  # provided by the loader at runtime
except ImportError:  # headless unit tests
    decky = None

HOME = os.path.expanduser("~")
TOGGLE = os.path.join(HOME, "AI", "singbox", "singbox-toggle.sh")
SERVER = os.path.join(HOME, "AI", "singbox", "singbox-server.sh")
MODE_FILE = os.path.join(HOME, "AI", "singbox", ".mode")
RAW = os.path.join(HOME, "AI", "neodon-sub", "raw.json")
SEL_SRV = os.path.join(HOME, "AI", "singbox", "selected-server.json")
QUOTA = os.path.join(HOME, "AI", "neodon-vpn", "sub-cache.json")
CONVERTER = os.path.join(HOME, "AI", "neodon-sub", "neodon-sub.py")

MODES = ("smart", "full")
ID_RE = re.compile(r"^[0-9]+$")

# Desktop preset display names (English, mirrors PRESETS in neodon-vpn.py).
# Game panel shows these so both UIs call rules by the same names.
PRESET_NAMES = {
    "default": "Default",
    "ru-bez-vpn": ".RU without VPN",
    "popular-ai": "Popular AI",
    "social-networks": "Social Networks",
    "only-unavailable": "Blocked-only",
    "socseti-vpn": "Social via VPN",
    "basic-set": "Basic Set",
}
USERINFO_RE = re.compile(r"upload=(\d+);\s*download=(\d+);\s*total=(\d+);\s*expire=(\d+)")


def _log(msg):
    try:
        if decky is not None:
            decky.logger.info("neodon-vpn: %s" % msg)
            return
    except Exception:
        pass
    print("neodon-vpn: %s" % msg, flush=True)


def _clean_env():
    # Decky >=3.1 ships LD_LIBRARY_PATH that breaks subprocess (libcrypto).
    env = dict(os.environ)
    env["LD_LIBRARY_PATH"] = ""
    return env


async def _run(argv, timeout):
    p = await asyncio.create_subprocess_exec(
        *argv, stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE, env=_clean_env())
    try:
        out, err = await asyncio.wait_for(p.communicate(), timeout)
    except asyncio.TimeoutError:
        try:
            p.kill()
        except ProcessLookupError:
            pass
        return 124, "", "timeout"
    return p.returncode or 0, out.decode("utf-8", "replace"), err.decode("utf-8", "replace")


def _read_json(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


async def get_status():
    """Live backend state (same oracle as the Desktop pill)."""
    rc, out, _ = await _run(["bash", TOGGLE, "status-json"], 15)
    if rc != 0:
        return {"ok": False, "error": out[-200:] if out else "status failed"}
    try:
        d = json.loads(out)
    except ValueError:
        return {"ok": False, "error": "bad status json"}
    d["ok"] = True
    prof = d.get("profile") or ""
    d["profile_name"] = PRESET_NAMES.get(prof, prof)
    return d


async def vpn_up():
    """Power on to last non-off mode (fallback smart)."""
    mode = "smart"
    try:
        with open(MODE_FILE, encoding="utf-8") as f:
            m = f.read().strip()
        if m in MODES:
            mode = m
    except OSError:
        pass
    rc, out, err = await _run(["bash", TOGGLE, mode], 30)
    return {"ok": rc == 0, "mode": mode, "out": (out or err)[-300:]}


async def vpn_down():
    rc, out, err = await _run(["bash", TOGGLE, "off"], 30)
    return {"ok": rc == 0, "out": (out or err)[-300:]}


async def set_mode(mode):
    if mode not in MODES:
        return {"ok": False, "error": "bad mode"}
    rc, out, err = await _run(["bash", TOGGLE, mode], 30)
    return {"ok": rc == 0, "mode": mode, "out": (out or err)[-300:]}


def _server_list():
    data = _read_json(RAW)
    if not isinstance(data, list):
        return []
    out = []
    for cfg in data:
        for o in cfg.get("outbounds") or []:
            if o.get("protocol") != "vless":
                continue
            s = ((o.get("settings") or {}).get("vnext") or [{}])[0]
            out.append({"remarks": cfg.get("remarks") or "",
                        "address": s.get("address")})
            break
    return out


async def get_servers():
    sel = _read_json(SEL_SRV) or {}
    # selected-server.json stores the key as "server" (not "address").
    return {"ok": True, "servers": _server_list(),
            "active": sel.get("server") or sel.get("address")}


async def set_server(idx):
    if not isinstance(idx, int) or isinstance(idx, bool):
        try:
            idx = int(idx)
        except (TypeError, ValueError):
            return {"ok": False, "error": "bad idx"}
    if not ID_RE.match(str(idx)):
        return {"ok": False, "error": "bad idx"}
    servers = _server_list()
    if not 0 <= idx < len(servers):
        return {"ok": False, "error": "idx out of range"}
    rc, out, err = await _run(["bash", SERVER, "set", str(idx)], 20)
    return {"ok": rc == 0, "out": (out or err)[-300:]}


async def get_quota():
    q = _read_json(QUOTA)
    if not isinstance(q, dict):
        return {"ok": False, "quota": None}
    return {"ok": True, "quota": q}


def _sub_url(path=None):
    """Subscription URL from our own converter file (regex, never exec)."""
    try:
        with open(path or CONVERTER, encoding="utf-8", errors="replace") as f:
            src = f.read()
    except OSError:
        return None
    m = re.search(r"^\s*URL\s*=\s*['\"]([^'\"]+)['\"]", src, re.M)
    return m.group(1) if m else None


def parse_userinfo(line):
    """'upload=..; download=..; total=..; expire=..' -> dict or None."""
    m = USERINFO_RE.search(line or "")
    if not m:
        return None
    up, down, total, expire = (int(x) for x in m.groups())
    used = up + down
    gb = lambda b: round(b / (1024 ** 3), 1)
    pct = round(used / total * 100) if total > 0 else 0
    exp = datetime.datetime.fromtimestamp(expire).strftime("Active until: %d %b %Y %H:%M")
    return {"pct": pct, "used": "%s GB / %s GB" % (gb(used), gb(total)),
            "expire": exp, "ts": int(datetime.datetime.now().timestamp())}


def _fetch_sub(url):
    jar = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    ua = {"User-Agent": "v2rayN/7.24.6"}

    def get(u):
        req = urllib.request.Request(u, headers=ua)
        with op.open(req, timeout=15) as r:
            return r.headers.get("subscription-userinfo", ""), r.read().decode("utf-8", "replace")

    userinfo, _ = get(url)          # pass 1: cookies + userinfo header
    _, body = get(url)              # pass 2: server list body
    return userinfo, body


async def refresh_sub():
    """Re-fetch subscription: servers + quota (same 2 passes as Desktop)."""
    url = _sub_url()
    if not url:
        return {"ok": False, "error": "no sub url"}
    try:
        userinfo, body = await asyncio.wait_for(
            asyncio.to_thread(_fetch_sub, url), 60)
    except Exception as e:
        return {"ok": False, "error": "fetch: %s" % str(e)[:120]}
    try:
        data = json.loads(body)
        assert isinstance(data, list) and data and "outbounds" in data[0]
    except (ValueError, AssertionError):
        return {"ok": False, "error": "bad sub body"}
    try:
        tmp = RAW + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(body)
        os.replace(tmp, RAW)
    except OSError as e:
        return {"ok": False, "error": "write: %s" % str(e)[:80]}
    info = parse_userinfo(userinfo)
    quota = None
    if info:
        try:
            with open(QUOTA, "w", encoding="utf-8") as f:
                json.dump(info, f)
            quota = info
        except OSError:
            pass
    return {"ok": True, "quota": quota,
            "servers": len(_server_list())}


class Plugin:
    async def _main(self):
        _log("backend up uid=%d home=%s" % (os.getuid(), HOME))

    async def _unload(self):
        pass

    async def get_status(self):
        r = await get_status()
        _log("get_status -> %s" % r.get("actual_state", r.get("error")))
        return r

    async def vpn_up(self):
        r = await vpn_up()
        _log("vpn_up -> ok=%s" % r.get("ok"))
        return r

    async def vpn_down(self):
        r = await vpn_down()
        _log("vpn_down -> ok=%s" % r.get("ok"))
        return r

    async def set_mode(self, mode):
        r = await set_mode(mode)
        _log("set_mode %s -> ok=%s" % (mode, r.get("ok")))
        return r

    async def get_servers(self):
        r = await get_servers()
        _log("get_servers -> n=%d" % len(r.get("servers", [])))
        return r

    async def set_server(self, idx):
        r = await set_server(idx)
        _log("set_server %s -> ok=%s" % (idx, r.get("ok")))
        return r

    async def get_quota(self):
        r = await get_quota()
        _log("get_quota -> ok=%s" % r.get("ok"))
        return r

    async def refresh_sub(self):
        r = await refresh_sub()
        _log("refresh_sub -> ok=%s" % r.get("ok"))
        return r
