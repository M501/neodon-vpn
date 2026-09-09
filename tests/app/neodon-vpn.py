#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Neodon V2 — v2RayTun-клон под Linux (Bazzite).
PySide6 GUI, один файл: логика из V1 + UI в стиле v2RayTun (Windows).
Режимы пользователя: OFF | PROXY (внутренний smart) | TUNNEL (внутренний full).
Бэкенд: neodon-hostctl / singbox-toggle.sh (НЕ менять).
"""

import json
import os
import re
import signal
import socket
import subprocess
import sys
import time

from PySide6.QtCore import Qt, QThread, QTimer, QSize, Signal, QEasingCurve
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QLabel, QPushButton,
                               QSystemTrayIcon, QMenu,
                               QVBoxLayout, QHBoxLayout, QStackedWidget, QFrame,
                               QListWidget, QListWidgetItem, QMessageBox,
                               QComboBox, QProgressBar, QRadioButton, QButtonGroup,
                               QCheckBox, QLineEdit, QScrollArea, QSizePolicy)
from PySide6.QtGui import QIcon, QColor, QPixmap
from PySide6.QtWidgets import (
    QApplication, QButtonGroup, QCheckBox, QComboBox, QDialog, QFrame, QGridLayout,
    QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem, QMainWindow,
    QPlainTextEdit, QProgressBar, QPushButton, QScrollArea, QSizePolicy, QStackedWidget,
    QVBoxLayout, QWidget,
)

HOME = os.path.expanduser("~")
BASE = os.path.join(HOME, "AI")
APP_DIR = os.path.join(BASE, "neodon-vpn")
RULES_JSON = os.path.join(APP_DIR, "app-rules.json")
HELPER = os.path.join(APP_DIR, "apply-app-rules.py")
CONVERTER = os.path.join(BASE, "neodon-sub", "neodon-sub.py")
RAW = os.path.join(BASE, "neodon-sub", "raw.json")
TOGGLE = os.path.join(BASE, "singbox", "singbox-toggle.sh")
SERVER_SCRIPT = os.path.join(BASE, "singbox", "singbox-server.sh")
SANDBOX = bool(os.environ.get("FLATPAK_ID"))
STATE_DIR = os.path.expanduser("~/.var/app/io.neodon.gui") if SANDBOX else APP_DIR
ACTION_HOOK = os.path.join(STATE_DIR, "gui-action.json")
SERVICES = ("sing-box.service", "sing-box-full.service", "sing-box-proxy.service")
GB = 1073741824
ENV = dict(os.environ, XDG_RUNTIME_DIR="/run/user/1000")

FLATPAK_MAP = {
    "org.mozilla.firefox": "firefox",
    "org.telegram.desktop": "telegram-desktop",
    "com.github.qbittorrent": "qbittorrent",
    "com.google.Chrome": "chrome",
    "io.github.zen_browser.zen": "zen",
    "app.haruna.Haruna": "haruna",
    "org.kde.okular": "okular",
    "org.kde.gwenview": "gwenview",
    "org.kde.kcalc": "kcalc",
    "com.github.tchx84.Flatseal": "flatseal",
    "io.github.flattool.Warehouse": "warehouse",
    "dev.opencode.Opencode": "opencode",
    "com.github.Matoking.protontricks": "protontricks",
    "io.github.v1993.ProtonPlus": "protonplus",
    "ru.linux_gaming.PortProton": "portproton",
    "io.github.ronniedroid.trayscale": "trayscale",
    "io.github.kontainer": "kontainer",
    "io.github.gearlever": "gearlever",
    "org.gnome.baobab": "baobab",
    "org.kde.filelight": "filelight",
    "io.github.vacuumtube": "vacuumtube",
}
FLAGS_DIR = os.path.join(APP_DIR, "flags")

# ---------------------------------------------------------------------------
# Пресеты правил сообщества (портированы из v2RayTun shared_preferences.json,
# 2026-08-19). Формат: (id, name, icon_emoji, description, verified,
#  global_proxy(bool), direct[], proxy[], block[])
# Правила Neodon-базовые (private/ozon/bittorrent/process) добавляются всегда.
# ---------------------------------------------------------------------------
PRESETS = [
    ("default", "Default", "🌐", "RU/торренты/Steam/Ozon напрямую, остальное — через VPN", False,
     True, [], [], []),
    ("ru-bez-vpn", ".RU без VPN", "🇷🇺", "Отправляет весь RU трафик без ВПН", True,
     True, ["domain:avito.st", "geosite:category-ru", "regexp:.*\\.ru$", "regexp:.*\\.xn--p1ai$"], [], []),

    ("popular-ai", "Popular AI", "🤖", "Популярные нейросети через VPN, остальной трафик мимо VPN", True,
     False, [], ["geosite:category-ai-!cn", "geosite:category-ai-cn"], []),
    ("social-networks", "Social Networks", "💬", "Популярные соцсети через VPN, остальной трафик напрямую", False,
     False, [], ["geosite:discord", "geosite:github", "geosite:google", "geosite:meta", "geosite:openai",
                 "geosite:spotify", "geosite:telegram", "geosite:tiktok", "geosite:vk", "geosite:whatsapp"], []),
    ("only-unavailable", "Только недоступные ресурсы", "🚫", "Через VPN только большинство недоступных в РФ ресурсов", False,
     False, [], ["geosite:anime", "geosite:anthropic", "geosite:artstation", "geosite:discord",
                 "geosite:google-gemini", "geosite:instagram", "geosite:linkedin", "geosite:meta",
                 "geosite:microsoft", "geosite:notion", "geosite:openai", "geosite:soundcloud",
                 "geosite:speedtest", "geosite:spotify", "geosite:tiktok", "geosite:twitch",
                 "geosite:twitter", "geosite:youtube"], []),
    ("socseti-vpn", "Соцсети через впн", "📱", "YouTube, Google, Instagram, TikTok, Discord, ChatGPT, WhatsApp, Telegram, Spotify через VPN", False,
     False, [], ["geosite:discord", "geosite:google", "geosite:instagram", "geosite:openai",
                 "geosite:spotify", "geosite:telegram", "geosite:tiktok", "geosite:whatsapp", "geosite:youtube"], []),
    ("basic-set", "Базовый набор", "🧩", "Instagram, YouTube, Telegram, WhatsApp, TikTok, Discord, ChatGPT", False,
     False, [], ["domain:1e100.net", "domain:bcvcdn.com", "domain:cdninstagram.com", "domain:chatgpt.com",
                 "domain:discord.com", "domain:discord.gg", "domain:discordapp.com", "domain:discordapp.net",
                 "domain:fbcdn.net", "domain:googlevideo.com", "domain:instagram.com", "domain:tiktok.tv",
                 "domain:twitch.tv", "domain:whatsapp.com", "domain:youtube.com", "domain:ytimg.com",
                 "geosite:cloudflare", "geosite:discord", "geosite:meta", "geosite:openai",
                 "geosite:telegram", "geosite:tiktok", "geosite:whatsapp", "geosite:youtube"], []),
]
# V1-наследие ai/anti-censorship удалено 2026-09-08 (spec 013): мусор не храним.

def preset_summary(direct, proxy):
    """One-line rule census for a preset card: counts only, no claims."""
    parts = []
    if direct:
        parts.append("напрямую: %d зап." % len(direct))
    if proxy:
        parts.append("через VPN: %d зап." % len(proxy))
    gs = sorted({e.split(":", 1)[1] for e in list(direct) + list(proxy)
                 if e.startswith("geosite:")})
    if gs:
        parts.append("категории: " + ", ".join(gs[:6]) + ("…" if len(gs) > 6 else ""))
    return " · ".join(parts) if parts else "без доп. записей"

ICONS_DIR = os.path.join(APP_DIR, "icons")

def preset_icon(pid):
    """v2RayTun icon file -> emoji -> letter. Returns (path, fallback)."""
    emo = "?"
    for p in PRESETS:
        if p[0] == pid:
            emo = p[2]
            break
    for ext in ("jpg", "png"):
        fp = os.path.join(ICONS_DIR, "%s.%s" % (pid, ext))
        if os.path.exists(fp):
            return fp, emo
    return "", emo

def card_pixmap(path, size=28):
    """Square crop-fill for photo icons with padding (v2RayTun black bars)."""
    pm = QPixmap(path)
    if pm.isNull():
        return None
    w, h = pm.width(), pm.height()
    s = min(w, h)
    pm = pm.copy((w - s) // 2, (h - s) // 2, s, s)
    return pm.scaled(size, size, Qt.AspectRatioMode.IgnoreAspectRatio,
                     Qt.TransformationMode.SmoothTransformation)

# Canaries: (domain, expected outbound) per preset. Shown live in the
# preset dialog against the APPLIED config; encoded from matrix_canary.py.
CANARIES = {
    "default": [("ozon.ru", "direct"), ("youtube.com", "proxy")],
    "ru-bez-vpn": [("ya.ru", "direct"), ("youtube.com", "proxy"), ("rutracker.org", "proxy")],
    "popular-ai": [("chatgpt.com", "proxy"), ("youtube.com", "direct")],
    "social-networks": [("vk.com", "proxy"), ("ya.ru", "direct")],
    "only-unavailable": [("youtube.com", "proxy"), ("ya.ru", "direct")],
    "socseti-vpn": [("youtube.com", "proxy"), ("google.com", "proxy")],
    "basic-set": [("instagram.com", "proxy"), ("ya.ru", "direct")],
}

_route_cache = {}

def route_lookup(domain, cfg_path=None):
    """Live lookup in the APPLIED sing-box config (what runs right now)."""
    import re as _re
    cfg_path = cfg_path or os.path.expanduser("~/AI/singbox/config.json")
    try:
        mt = os.path.getmtime(cfg_path)
    except OSError:
        return "?", "no-config"
    c = _route_cache.get(cfg_path)
    if c is None or mt != c["mtime"]:
        try:
            d = json.load(open(cfg_path))
            c = {"rules": d["route"]["rules"],
                 "final": d["route"].get("final", "proxy"), "mtime": mt}
            _route_cache[cfg_path] = c
        except (OSError, ValueError, KeyError):
            return "?", "bad-config"
    dom = (domain or "").lower().strip().rstrip(".")
    for r in c["rules"]:
        if "domain" in r and dom in (x.lower() for x in r["domain"]):
            return r.get("outbound", "?"), "domain"
        if "domain_suffix" in r and any(
                dom == s.lower() or dom.endswith("." + s.lower())
                for s in r["domain_suffix"]):
            return r.get("outbound", "?"), "suffix"
        if "domain_keyword" in r and any(k.lower() in dom for k in r["domain_keyword"]):
            return r.get("outbound", "?"), "keyword"
        if "domain_regex" in r and any(_re.compile(p).search(dom) for p in r["domain_regex"]):
            return r.get("outbound", "?"), "regex"
    return c["final"], "final"

# ---------------------------------------------------------------------------
# Иконки (SVG, в стиле v2RayTun: тонкие линии, текущий цвет)
# ---------------------------------------------------------------------------
def _svg(path_d, view="0 0 24 24", fill="none", stroke="currentColor", sw=1.8):
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="%s" fill="%s" stroke="%s" '
            'stroke-width="%s" stroke-linecap="round" stroke-linejoin="round">%s</svg>'
            % (view, fill, stroke, sw, path_d))

ICONS = {
    "home": _svg('<path d="M3 10.5 12 3l9 7.5"/><path d="M5 9.5V21h14V9.5"/><path d="M9.5 21v-6h5v6"/>'),
    "settings": _svg('<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 1 1-4 0v-.09a1.65 1.65 0 0 0-1-1.51 1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 1 1 0-4h.09a1.65 1.65 0 0 0 1.51-1 1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33h.01a1.65 1.65 0 0 0 1-1.51V3a2 2 0 1 1 4 0v.09a1.65 1.65 0 0 0 1 1.51h.01a1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82v.01a1.65 1.65 0 0 0 1.51 1H21a2 2 0 1 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>'),
    "logs": _svg('<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6"/><path d="M8 13h8"/><path d="M8 17h5"/>'),
    "info": _svg('<circle cx="12" cy="12" r="9"/><path d="M12 16v-5"/><path d="M12 8h.01"/>'),
    "power": _svg('<path d="M12 2v10"/><path d="M18.36 6.64a9 9 0 1 1-12.72 0"/>'),
    "refresh": _svg('<path d="M21 12a9 9 0 1 1-2.64-6.36"/><path d="M21 3v6h-6"/>'),
    "back": _svg('<path d="M15 18l-6-6 6-6"/>'),
    "forward": _svg('<path d="M9 18l6-6-6-6"/>'),
    "link": _svg('<path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>'),
    "lock": _svg('<rect x="4" y="11" width="16" height="10" rx="2"/><path d="M8 11V7a4 4 0 0 1 8 0v4"/>'),
    "web": _svg('<circle cx="12" cy="12" r="9"/><path d="M3 12h18"/><path d="M12 3a15 15 0 0 1 0 18 15 15 0 0 1 0-18"/>'),
    "check": _svg('<path d="M20 6 9 17l-5-5"/>'),
    "download": _svg('<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><path d="M7 10l5 5 5-5"/><path d="M12 15V3"/>'),
    "filter": _svg('<path d="M22 3H2l8 9.46V19l4 2v-8.54z"/>'),
    "export": _svg('<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><path d="M7 10l5-5 5 5"/><path d="M12 15V5"/>'),
    "clear": _svg('<path d="M3 6h18"/><path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/>'),
    "folder": _svg('<path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>'),
    "route": _svg('<path d="M4 19h16"/><path d="M8 12h8"/><path d="M12 5v14"/>'),
    "plus": _svg('<path d="M12 5v14"/><path d="M5 12h14"/>'),
    "dots": _svg('<circle cx="5" cy="12" r="1.6"/><circle cx="12" cy="12" r="1.6"/><circle cx="19" cy="12" r="1.6"/>'),
    "flag": _svg('<path d="M4 21V4"/><path d="M4 4c5-3 10 3 16 0v9c-6 3-11-3-16 0"/>'),
}


def icon_pixmap(name, size=22, color="#9B9BA5"):
    from PySide6.QtCore import QByteArray
    from PySide6.QtGui import QPainter, QPixmap
    from PySide6.QtSvg import QSvgRenderer
    svg = ICONS.get(name, ICONS["info"]).replace("currentColor", color)
    renderer = QSvgRenderer(QByteArray(svg.encode()))
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    renderer.render(p)
    p.end()
    return pm


# ---------------------------------------------------------------------------
# QSS — дизайн v2RayTun (тёмная тема, Inter, синий акцент)
# ---------------------------------------------------------------------------
QSS = """
* { font-family: 'Inter', 'Segoe UI', 'DejaVu Sans', sans-serif; }
QMainWindow, QDialog, #root { background: #0F0F13; }
QWidget { color: #F5F5F7; font-size: 13px; }
#sidebar { background: #17171C; border-right: 1px solid #26262E; }
#sidebarBtn { border: none; border-radius: 10px; background: transparent; }
#sidebarBtn:hover { background: #26262E; }
#sidebarBtn:checked { background: #2A5FD8; }
#sidebarBtn:checked:hover { background: #3373F7; }
#page { background: #0F0F13; }
#card { background: #17171C; border: 1px solid #26262E; border-radius: 14px; }
#card:hover { border-color: #33333D; }
#title { font-size: 12px; font-weight: 700; color: #9B9BA5; letter-spacing: 1px; }
#h1 { font-size: 15px; font-weight: 700; color: #F5F5F7; }
#h2 { font-size: 13px; font-weight: 600; color: #F5F5F7; }
#muted { color: #9B9BA5; }
#timer { font-size: 36px; font-weight: 800; color: #F5F5F7; font-family: 'JetBrains Mono', 'Cascadia Mono', 'DejaVu Sans Mono', monospace; }
QPushButton { border: none; border-radius: 10px; padding: 8px 14px; font-weight: 600; background: #26262E; color: #F5F5F7; }
QPushButton:hover { background: #33333D; }
QPushButton:pressed { background: #1F1F26; }
QPushButton:disabled { color: #6B6B76; background: #1A1A20; }
#accent { background: #3373F7; color: #FFFFFF; }
#accent:hover { background: #2A5FD8; }
#ghost { background: transparent; color: #9B9BA5; border: 1px solid #33333D; }
#ghost:hover { color: #F5F5F7; border-color: #4A4A55; }
#danger { background: #E5484D; color: #FFF; }
#danger:hover { background: #C93A3F; }
#powerBtn { border-radius: 42px; background: #26262E; border: 2px solid #33333D; }
#powerBtn:hover { border-color: #4A4A55; }
#powerBtn:checked { background: #2A5FD8; border-color: #3373F7; }
#modeOn { background: #3373F7; color: #FFFFFF; min-height: 40px; font-size: 13px; font-weight: 700; border-radius: 10px; }
#modeOn:hover { background: #2A5FD8; }
#modeOff { background: #1F1F26; color: #9B9BA5; min-height: 40px; font-size: 13px; font-weight: 700; border-radius: 10px; }
#modeOff:hover { background: #26262E; color: #F5F5F7; }
#statusPill { border-radius: 14px; padding: 6px 16px; font-weight: 700; font-size: 13px; }
#statusOff { background: #26262E; color: #9B9BA5; }
#statusOk { background: #1C3D2E; color: #4ADE80; }
#statusWarn { background: #3D2E1C; color: #F5A524; }
#statusErr { background: #3D1C1E; color: #F87171; }
#rowBtn { background: transparent; border: none; border-radius: 12px; text-align: left; }
#rowBtn:hover { background: #1F1F26; }
#rowCard { background: #17171C; border: 1px solid #26262E; border-radius: 12px; }
#rowCard:hover { background: #1F1F26; border-color: #33333D; }
#rowCardActive { background: #17171C; border: 2px solid #3373F7; border-radius: 12px; }
#badge { background: #1F1F26; border: 1px solid #33333D; border-radius: 14px; color: #3373F7; font-size: 13px; font-weight: 700; }
#activeTag { color: #4ADE80; font-weight: 700; font-size: 12px; }
QProgressBar { background: #1F1F26; border: none; border-radius: 5px; min-height: 10px; max-height: 10px; text-align: center; color: transparent; }
QProgressBar::chunk { background: #3373F7; border-radius: 5px; }
QListWidget { background: transparent; border: none; outline: 0; }
QListWidget::item { border-radius: 10px; }
QListWidget::item:selected { background: #26262E; }
QScrollArea { background: transparent; border: none; }
QScrollArea > QWidget > QWidget { background: transparent; }
QScrollBar:vertical { background: transparent; width: 8px; }
QScrollBar::handle:vertical { background: #33333D; border-radius: 4px; min-height: 24px; }
QScrollBar::add-line, QScrollBar::sub-line { height: 0; }
QComboBox { background: #1F1F26; border: 1px solid #33333D; border-radius: 10px; padding: 7px 12px; }
QComboBox::drop-down { border: none; width: 24px; }
QComboBox QAbstractItemView { background: #1F1F26; border: 1px solid #33333D; selection-background-color: #2A5FD8; }
QLineEdit { background: #1F1F26; border: 1px solid #33333D; border-radius: 10px; padding: 8px 12px; }
QPlainTextEdit { background: #0B0B0E; border: 1px solid #26262E; border-radius: 10px; color: #9B9BA5; font-family: 'Cascadia Mono', 'JetBrains Mono', monospace; font-size: 11px; }
QCheckBox { spacing: 8px; }
QCheckBox::indicator { width: 18px; height: 18px; border-radius: 5px; border: 1px solid #4A4A55; background: #16161E; }
QCheckBox::indicator:hover { border-color: #3373F7; }
QCheckBox::indicator:checked { background: #3373F7; border-color: #3373F7; }
#hint { color: #6B6B76; font-size: 12px; }
"""

# ---------------------------------------------------------------------------
# Бэкенд-хелперы (V1, без изменений)
# ---------------------------------------------------------------------------

def host_cmd(cmd):
    return "flatpak-spawn --host " + cmd if SANDBOX else cmd


def run_cmd(cmd, timeout=10):
    try:
        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, text=True, env=ENV,
                             start_new_session=True)
    except Exception as e:
        return -1, "", str(e)
    try:
        out, err = p.communicate(timeout=timeout)
        return p.returncode, (out or "").strip(), (err or "").strip()
    except subprocess.TimeoutExpired:
        try:
            os.killpg(os.getpgid(p.pid), signal.SIGTERM)
        except (ProcessLookupError, PermissionError):
            pass
        try:
            out, err = p.communicate(timeout=2)
            return -1, (out or "").strip(), "timeout"
        except subprocess.TimeoutExpired:
            try:
                os.killpg(os.getpgid(p.pid), signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                pass
            out, err = p.communicate()
            return -1, (out or "").strip(), "timeout"


def converter_consts():
    url = ua = raw = None
    try:
        src = open(CONVERTER).read()
    except OSError:
        src = ""
    for name in ("URL", "UA", "RAW"):
        m = re.search(r"^\s*%s\s*=\s*['\"]([^'\"]+)['\"]" % name, src, re.M)
        if name == "URL":
            url = m.group(1) if m else None
        elif name == "UA":
            ua = m.group(1) if m else None
        else:
            raw = m.group(1) if m else RAW
    return url, ua, raw or RAW


def load_servers():
    try:
        data = json.load(open(RAW))
    except Exception:
        return []
    out = []
    for cfg in data:
        for o in cfg.get("outbounds") or []:
            if o.get("protocol") != "vless":
                continue
            s = ((o.get("settings") or {}).get("vnext") or [{}])[0]
            st = o.get("streamSettings") or {}
            out.append({
                "remarks": cfg.get("remarks") or "",
                "address": s.get("address"),
                "port": s.get("port"),
                "network": st.get("network") or "tcp",
                "security": st.get("security") or "none",
            })
            break
    return out


def current_mode():
    cmd = host_cmd("neodon-hostctl status") if SANDBOX else "bash %s status" % TOGGLE
    rc, out, err = run_cmd(cmd, timeout=10)
    if "FULL" in out:
        return "full"
    if "SMART" in out or "PROXY" in out:
        return "smart"
    return "off"


def active_epoch():
    for svc in SERVICES:
        rc, ts, _ = run_cmd(host_cmd("systemctl --user show -p ActiveEnterTimestamp --value %s" % svc))
        if rc == 0 and ts and ts != "n/a":
            rc2, ep, _ = run_cmd("date -d '%s' +%%s" % ts)
            if rc2 == 0 and ep.isdigit():
                return int(ep)
    return None


_FLAG_EMOJI = {chr(0x1F1E6 + i): chr(0x41 + i) for i in range(26)}


def flag_code(remark):
    m = re.search(r"\[([A-Za-z]{2})", remark or "")
    if m:
        return m.group(1).upper()
    for em, code in _FLAG_EMOJI.items():
        if em in (remark or ""):
            return code
    return None


def strip_flags(text):
    return "".join(ch for ch in (text or "") if ch not in _FLAG_EMOJI)


def flag_pixmap(code, w=24, h=16):
    if not code:
        return None
    pix = QPixmap(os.path.join(FLAGS_DIR, code + ".png"))
    if pix.isNull():
        return None
    return pix.scaled(w, h, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)


def server_desc(s):
    sec = {"reality": "Reality", "none": "plain"}.get((s.get("security") or "none").lower(), "TLS")
    net = {"tcp": "TCP", "ws": "WS", "grpc": "gRPC"}.get((s.get("network") or "tcp").lower(), "?")
    return "VLESS · %s · %s" % (sec, net)


def parse_sub_info(line):
    d = {}
    body = line.split(":", 1)[1] if ":" in line else line
    for kv in body.split(";"):
        if "=" in kv:
            k, v = kv.strip().split("=", 1)
            if v.strip().isdigit():
                d[k.strip().lower()] = int(v.strip())
    return d


def sub_used_total(info):
    if not info:
        return 0, 0
    used = info.get("upload", 0) + info.get("download", 0)
    return used, info.get("total", 0)


def sub_summary(info):
    used, total = sub_used_total(info)
    if total <= 0:
        return "N/A"
    return "%.1f GB / %.0f GB" % (used / GB, total / GB)


def sub_used_pct(info):
    used, total = sub_used_total(info)
    if total <= 0:
        return 0
    return max(0, min(100, int(used * 100 / total)))


def sub_expire(info):
    if not info or info.get("expire", 0) <= 0:
        return "Active until: —"
    return "Active until: " + time.strftime("%d %b %Y %H:%M", time.localtime(info["expire"]))


# ---------------------------------------------------------------------------
# Workers (V1)
# ---------------------------------------------------------------------------

class CmdWorker(QThread):
    ok = Signal(str)
    fail = Signal(str)

    def __init__(self, cmd, timeout=20):
        super().__init__()
        self.cmd = cmd
        self.timeout = timeout

    def run(self):
        rc, out, err = run_cmd(self.cmd, self.timeout)
        if rc == 0:
            self.ok.emit(out)
        else:
            self.fail.emit(err or out or "ошибка")


class ToggleWorker(QThread):
    done = Signal(bool, str)

    def __init__(self, mode):
        super().__init__()
        self.mode = mode

    def run(self):
        if SANDBOX:
            cmd = host_cmd("neodon-hostctl stop" if self.mode == "off" else "neodon-hostctl start %s" % self.mode)
        else:
            cmd = "bash %s %s" % (TOGGLE, self.mode)
        rc, out, err = run_cmd(cmd, 25)
        self.done.emit(rc == 0, out or err)


class SelectWorker(QThread):
    done = Signal(bool, str)
    phase = Signal(str)

    def __init__(self, idx, start_after=False, mode="smart"):
        super().__init__()
        self.idx = idx
        self.start_after = start_after
        self.mode = mode

    def run(self):
        cmd = host_cmd("neodon-hostctl server %d" % self.idx) if SANDBOX else "bash %s set %d" % (SERVER_SCRIPT, self.idx)
        self.phase.emit("Смена сервера…")
        rc, out, err = run_cmd(cmd, 10)
        if rc != 0:
            self.done.emit(False, out or err or "не удалось сменить сервер")
            return
        if self.start_after:
            self.phase.emit("Сервер выбран, подключение…")
            cmd2 = host_cmd("neodon-hostctl start %s" % self.mode) if SANDBOX else "bash %s %s" % (TOGGLE, self.mode)
            rc2, out2, err2 = run_cmd(cmd2, 12)
            if rc2 != 0:
                self.done.emit(False, out2 or err2 or "не удалось подключиться")
                return
        self.done.emit(True, out)


class PingWorker(QThread):
    result = Signal(int, int)
    done = Signal()

    def __init__(self, servers):
        super().__init__()
        self.servers = servers

    def run(self):
        for i, s in enumerate(self.servers):
            t0 = time.monotonic()
            try:
                with socket.create_connection((s["address"], s["port"]), timeout=2):
                    self.result.emit(i, round((time.monotonic() - t0) * 1000))
            except Exception:
                self.result.emit(i, -1)
        self.done.emit()


def _fast_poll_wanted(new_state, deadline, now):
    """Burst polls during transition instead of waiting out the 8s timer."""
    return new_state in ("TRANSITIONING", "CONNECTING", "STARTING", "DEGRADED") and now < deadline


# ---------------------------------------------------------------------------
# UI: виджеты
# ---------------------------------------------------------------------------

class IconButton(QPushButton):
    def __init__(self, icon_name, size=22, color="#9B9BA5", parent=None, checkable=False,
                 checked_color="#FFFFFF", object_name="sidebarBtn", tip=None):
        super().__init__(parent)
        self._icon_name = icon_name
        self._color = color
        self._checked_color = checked_color
        self.setObjectName(object_name)
        self.setCheckable(checkable)
        if tip:
            self.setToolTip(tip)
        self.setFixedSize(46, 46)
        self.setIconSize(QSize(size, size))
        self._apply_icon()

    def _apply_icon(self):
        color = self._checked_color if (self.isCheckable() and self.isChecked()) else self._color
        from PySide6.QtGui import QIcon
        self.setIcon(QIcon(icon_pixmap(self._icon_name, self.iconSize().width(), color)))

    def setChecked(self, checked):
        super().setChecked(checked)
        self._apply_icon()


class StatusPill(QLabel):
    def set_state(self, state):
        st = {
            "CONNECTED": ("Connected", "statusOk"),
            "STARTING": ("Connecting…", "statusWarn"),
            "CONNECTING": ("Connecting…", "statusWarn"),
            "TRANSITIONING": ("Switching…", "statusWarn"),
            "STOPPING": ("Stopping…", "statusWarn"),
            "DEGRADED": ("Reconnecting…", "statusWarn"),
            "LOCKED": ("Protected — VPN unavailable", "statusWarn"),
            "FAILED": ("Failed", "statusErr"),
        }.get(state, ("Not connected", "statusOff"))
        self.setText(st[0])
        self.setObjectName(st[1] + " statusPill")
        self.style().unpolish(self)
        self.style().polish(self)


def ensure_rules():
    if not os.path.exists(RULES_JSON):
        try:
            os.makedirs(APP_DIR, exist_ok=True)
            with open(RULES_JSON, "w") as f:
                f.write(json.dumps({"direct": ["qbittorrent"]}, indent=2) + "\n")
        except OSError:
            pass


# ---------------------------------------------------------------------------
# Главное окно
# ---------------------------------------------------------------------------

class _ElidedLabel(QLabel):
    """Single-line label with … at any DPI (QLabel has no setElideMode)."""
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setWordWrap(False)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

    def paintEvent(self, e):
        from PySide6.QtGui import QPainter
        p = QPainter(self)
        el = self.fontMetrics().elidedText(
            self.text(), Qt.TextElideMode.ElideRight, max(0, self.contentsRect().width()))
        self.style().drawItemText(p, self.contentsRect(), self.alignment(),
                                  self.palette(), True, el)

    def minimumSizeHint(self):
        # let the grid shrink us (elide paints …); default hint = full text
        return QSize(0, self.fontMetrics().height())


class _ClickFrame(QFrame):
    """Кликабельный QFrame (карточка-кнопка): QLabel-контент рендерится,
    в отличие от QPushButton с layout (там дочерние QLabel пропадают).
    Tap-vs-drag: скролл заканчивается тем же release — без slop любой
    отпуск пальца стрелял бы как тап. Порог 12px по Манхэттену."""
    TAP_SLOP_PX = 12

    def __init__(self, on_click, parent=None):
        super().__init__(parent)
        self._cb = on_click
        self._press_pos = None

    def mousePressEvent(self, e):
        try:
            self._press_pos = e.position().toPoint()
        except Exception:
            self._press_pos = None
        super().mousePressEvent(e)

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton and self.rect().contains(e.position().toPoint()):
            pos = e.position().toPoint()
            start = self._press_pos
            if start is None or (pos - start).manhattanLength() <= self.TAP_SLOP_PX:
                self._cb()
        self._press_pos = None
        super().mouseReleaseEvent(e)



def _enable_kinetic(scroll_area):
    """Single kinetic-scroll helper (touch-only so taps always pass through).
    ponytail: one place — tune Delay/Distance here if feel is off."""
    try:
        from PySide6.QtWidgets import QScroller, QScrollerProperties
        vp = scroll_area.viewport()
        QScroller.grabGesture(vp, QScroller.ScrollerGestureType.TouchGesture)
        sp = QScroller.scroller(vp)
        props = sp.scrollerProperties()
        props.setScrollMetric(QScrollerProperties.ScrollMetric.MousePressEventDelay, 0.06)
        props.setScrollMetric(QScrollerProperties.ScrollMetric.DragStartDistance, 0.012)
        props.setScrollMetric(QScrollerProperties.ScrollMetric.VerticalOvershootPolicy, QScrollerProperties.OvershootPolicy.OvershootAlwaysOff)
        props.setScrollMetric(QScrollerProperties.ScrollMetric.HorizontalOvershootPolicy, QScrollerProperties.OvershootPolicy.OvershootAlwaysOff)
        sp.setScrollerProperties(props)
    except Exception:
        pass

class MainWindow(QMainWindow):
    MODE_LABELS = {"full": "TUNNEL", "smart": "PROXY", "proxy": "PROXY"}

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Neodon VPN")
        self.resize(720, 700)
        self.setMinimumSize(620, 680)
        self._restore_geom()
        self.servers = []
        self.lats = {}
        self._workers = []
        self._op_in_progress = False
        self._poll_busy = False
        self._fast_poll_until = 0
        self._last_desired = None
        self._settle_until = 0
        self._pending = None
        self._last_preset = None
        self.connected = False
        self.mode = "smart"          # пользовательский: smart (PROXY) | full (TUNNEL)
        self.status = {}
        self.state = "OFF"
        self.desired = "smart"
        self.active_profile = "default"
        self.active_addr = None
        ensure_rules()
        self._build_ui()
        self._setup_tray()
        self.set_mode(current_mode() if current_mode() in ("smart", "full") else "smart")
        self.refresh_active_server()
        self.reload_servers()
        self.timer_q = QTimer(self)
        self.timer_q.timeout.connect(self.tick)
        self.timer_q.start(1000)
        self.poll_timer = QTimer(self)
        self.poll_timer.timeout.connect(self.poll_status)
        self.poll_timer.start(8000)
        self.sub_timer = QTimer(self)
        self.sub_timer.timeout.connect(self.refresh_sub)
        self.sub_timer.start(1800000)
        self.render_presets()
        self.refresh_sub()  # auto-refresh on every GUI start
        self.poll_status()

    # ---- каркас ----
    def _build_ui(self):
        central = QWidget(self)
        central.setObjectName("root")
        self.setCentralWidget(central)
        lay = QHBoxLayout(central)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        # sidebar
        side = QWidget()
        side.setObjectName("sidebar")
        side.setFixedWidth(58)
        sl = QVBoxLayout(side)
        sl.setContentsMargins(6, 10, 6, 10)
        sl.setSpacing(6)
        self.nav_btns = {}
        for key, icon, tip in (("home", "home", "Главная"),
                               ("settings", "settings", "Настройки"),
                               ("logs", "logs", "Логи"),
                               ("apps", "folder", "Приложения")):
            b = IconButton(icon, tip=tip)
            b.setToolTip(tip)
            b.setCheckable(True)
            b.clicked.connect(lambda _=False, k=key: self.navigate(k))
            sl.addWidget(b)
            self.nav_btns[key] = b
        sl.addStretch()
        info = IconButton("info", color="#6B6B76", object_name="sidebarBtn")
        info.setToolTip("О программе")
        info.clicked.connect(lambda: self.navigate("about"))
        sl.addWidget(info)

        # stack
        self.stack = QStackedWidget()
        self.pages = {}
        self._build_home()
        self._build_traffic()
        self._build_settings()
        self._build_logs()
        self._build_apps()
        self._build_about()
        lay.addWidget(side)
        lay.addWidget(self.stack, 1)
        self.navigate("home")

    def navigate(self, key):
        order = {"home": 0, "traffic": 1, "settings": 2, "logs": 3, "apps": 4, "about": 5}
        idx = order.get(key)
        if idx is None:
            return
        self.stack.setCurrentIndex(idx)
        active_map = {"home": "home", "settings": "settings", "logs": "logs", "apps": "apps"}
        for k, b in self.nav_btns.items():
            b.setChecked(k == active_map.get(key))
        if key == "logs":
            self.refresh_logs()
        if key == "apps":
            self.apps_page.refresh()

    def _page(self, title, scrollable=True):
        w = QWidget()
        w.setObjectName("page")
        outer = QVBoxLayout(w)
        outer.setContentsMargins(0, 0, 0, 0)
        hdr = QHBoxLayout()
        hdr.setContentsMargins(14, 12, 14, 4)
        t = QLabel(title)
        t.setObjectName("h1")
        hdr.addWidget(t)
        hdr.addStretch()
        outer.addLayout(hdr)
        if scrollable:
            body = QScrollArea()
            body.setWidgetResizable(True)
            # touch: drag anywhere to scroll (kinetic, single helper)
            _enable_kinetic(body)
            body.setFrameShape(QFrame.Shape.NoFrame)
            cont = QWidget()
            bl = QVBoxLayout(cont)
            bl.setContentsMargins(14, 6, 14, 14)
            bl.setSpacing(10)
            body.setWidget(cont)
            outer.addWidget(body, 1)
            return w, bl
        bl = QVBoxLayout()
        bl.setContentsMargins(14, 6, 14, 14)
        bl.setSpacing(10)
        outer.addLayout(bl, 1)
        return w, bl

    # ---- Home ----
    def _build_home(self):
        w, bl = self._page("Connection time")
        self.stack.addWidget(w)
        self.pages["home"] = w

        self.timer_lbl = QLabel("00:00:00")
        self.timer_lbl.setObjectName("timer")
        self.timer_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bl.addWidget(self.timer_lbl)

        self.power = QPushButton()
        self.power.setObjectName("powerBtn")
        self.power.setFixedSize(84, 84)
        self.power.setCheckable(True)
        self.power.setIconSize(QSize(34, 34))
        self.power.setCursor(Qt.CursorShape.PointingHandCursor)
        self.power.clicked.connect(self.on_power)
        hb = QHBoxLayout()
        hb.addStretch()
        hb.addWidget(self.power)
        hb.addStretch()
        bl.addLayout(hb)

        self.pill = StatusPill()
        self.pill.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bl.addWidget(self.pill, 0, Qt.AlignmentFlag.AlignHCenter)

        self.state_meta = QLabel("")
        self.state_meta.setObjectName("muted")
        self.state_meta.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.state_meta.setWordWrap(True)
        bl.addWidget(self.state_meta)

        # VPN mode
        mode_card, ml = self._card(bl, "VPN MODE")
        mrow = QHBoxLayout()
        mrow.setSpacing(8)
        self.btn_proxy = QPushButton("PROXY")
        self.btn_tunnel = QPushButton("TUNNEL")
        self.btn_proxy.setCheckable(True)
        self.btn_tunnel.setCheckable(True)
        self.mode_group = QButtonGroup(self)
        self.mode_group.setExclusive(True)
        self.mode_group.addButton(self.btn_proxy)
        self.mode_group.addButton(self.btn_tunnel)
        self.btn_proxy.clicked.connect(lambda: self.set_mode("smart", restart=True))
        self.btn_tunnel.clicked.connect(lambda: self.set_mode("full", restart=True))
        mrow.addWidget(self.btn_proxy)
        mrow.addWidget(self.btn_tunnel)
        ml.addLayout(mrow)

        # карточки Traffic rules / Routing
        tr = self._row_card(bl, "folder", "Traffic rules", "Пресеты правил сообщества",
                            lambda: self.navigate("traffic"))
        # Routing убран: дубль Traffic rules (фиктивный дубликат)

        # серверы
        sc, sl = self._card(bl, "SERVERS")
        subrow = QHBoxLayout()
        subdot = QLabel("●")
        subdot.setStyleSheet("color:#E5484D; font-size:13px;")
        self.sub_name = QLabel("NEODON VPN")
        self.sub_name.setObjectName("h2")
        self.sub_refresh_btn = QPushButton()
        self.sub_refresh_btn.setIcon(QIcon(icon_pixmap("refresh", 18, "#9B9BA5")))
        self.sub_refresh_btn.setObjectName("ghost")
        self.sub_refresh_btn.setFixedSize(30, 30)
        self.sub_refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.sub_refresh_btn.setToolTip("Обновить подписку")
        self.sub_refresh_btn.clicked.connect(self.refresh_sub)
        self._refresh_btns = getattr(self, "_refresh_btns", []) + [self.sub_refresh_btn]
        subrow.addWidget(subdot)
        subrow.addWidget(self.sub_name)
        subrow.addStretch()
        self.sub_ping_btn = QPushButton("Пинг")
        self.sub_ping_btn.setObjectName("ghost")
        self.sub_ping_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.sub_ping_btn.clicked.connect(self.start_ping)
        subrow.addWidget(self.sub_ping_btn)
        subrow.addWidget(self.sub_refresh_btn)
        sl.addLayout(subrow)
        self.sub_progress = QProgressBar()
        self.sub_progress.setRange(0, 100)
        self.sub_progress.setValue(0)
        self.sub_progress.setTextVisible(False)
        sl.addWidget(self.sub_progress)
        qrow = QHBoxLayout()
        self.sub_used = QLabel("N/A")
        self.sub_used.setObjectName("h2")
        self.sub_expire = QLabel(sub_expire(None))
        self.sub_expire.setObjectName("muted")
        qrow.addWidget(self.sub_used)
        qrow.addStretch()
        qrow.addWidget(self.sub_expire)
        sl.addLayout(qrow)
        hint2 = QLabel("Нажмите ↻, если не работает VPN")
        hint2.setObjectName("hint")
        sl.addWidget(hint2)
        # servers: 2-column grid inside main scroll — no inner scroll, drag anywhere scrolls page
        self.srv_container = QWidget()
        self.srv_grid = QGridLayout(self.srv_container)
        self.srv_grid.setContentsMargins(0, 0, 0, 0)
        self.srv_grid.setSpacing(8)
        self.srv_grid.setAlignment(Qt.AlignmentFlag.AlignTop)
        sl.addWidget(self.srv_container)

        hint = QLabel("Нажмите на сервер, чтобы подключиться или сменить его. Если VPN не работает — переключите сервер или нажмите ↻.")
        hint.setObjectName("hint")
        hint.setWordWrap(True)
        bl.addWidget(hint)
        bl.addStretch()
        self._apply_power_icon()

    def _card(self, bl, title):
        frame = QFrame()
        frame.setObjectName("card")
        lay = QVBoxLayout(frame)
        lay.setContentsMargins(14, 10, 14, 12)
        lay.setSpacing(8)
        t = QLabel(title)
        t.setObjectName("title")
        lay.addWidget(t)
        bl.addWidget(frame)
        return frame, lay

    def _row_card(self, bl, icon, title, sub, on_click):
        # QFrame вместо QPushButton: QLabel-контент внутри QPushButton с layout
        # не рендерится (текст пропадает) — frame рендерит гарантированно.
        btn = _ClickFrame(on_click)
        btn.setObjectName("rowCard")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        hl = QHBoxLayout(btn)
        hl.setContentsMargins(12, 12, 12, 12)
        hl.setSpacing(10)
        ic = QLabel()
        ic.setPixmap(icon_pixmap(icon, 20, "#3373F7"))
        hl.addWidget(ic)
        v = QVBoxLayout()
        t = QLabel(title)
        t.setObjectName("h2")
        s = QLabel(sub)
        s.setObjectName("muted")
        v.addWidget(t)
        v.addWidget(s)
        hl.addLayout(v, 1)
        ar = QLabel()
        ar.setPixmap(icon_pixmap("forward", 18, "#9B9BA5"))
        hl.addWidget(ar)
        bl.addWidget(btn)
        return btn

    # ---- Traffic rules ----
    def _build_traffic(self):
        w, bl = self._page("Traffic rules")
        self.stack.addWidget(w)
        self.pages["traffic"] = w
        desc = QLabel("Пресет правил под свои нужды. Тап — применить; активный подсвечен. Режим TUNNEL игнорирует правила.")
        desc.setObjectName("muted")
        desc.setWordWrap(True)
        bl.addWidget(desc)
        use_row = QFrame()
        use_row.setObjectName("rowCard")
        uh = QHBoxLayout(use_row)
        uh.setContentsMargins(12, 10, 12, 10)
        ul = QLabel("Use preset")
        ul.setObjectName("h2")
        uh.addWidget(ul)
        uh.addStretch(1)
        self.use_preset_cb = QCheckBox()
        self.use_preset_cb.setToolTip("Выкл — базовый набор Default")
        self.use_preset_cb.toggled.connect(self.on_use_preset)
        uh.addWidget(self.use_preset_cb)
        bl.addWidget(use_row)
        info = QLabel("Community rules — готовые правила от сообщества под разные нужды.")
        info.setObjectName("muted")
        info.setWordWrap(True)
        bl.addWidget(info)
        self.preset_btns = {}
        for pid, name, icon, descr, verified, gproxy, direct, proxy, block in PRESETS:
            b = _ClickFrame(lambda p=pid: self.select_preset(p))
            b.setObjectName("rowCard")
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            hl = QHBoxLayout(b)
            hl.setContentsMargins(12, 10, 12, 10)
            hl.setSpacing(10)
            ipath, ifallback = preset_icon(pid)
            px = card_pixmap(ipath) if ipath else None
            if px is None:
                ic = QLabel(ifallback or icon or "•")
                ic.setStyleSheet("font-size: 18px;")
            else:
                ic = QLabel()
                ic.setPixmap(px)
            ic.setFixedSize(28, 28)
            ic.setAlignment(Qt.AlignmentFlag.AlignCenter)
            hl.addWidget(ic)
            v = QVBoxLayout()
            nh = QHBoxLayout()
            nm = QLabel(name)
            nm.setObjectName("h2")
            nh.addWidget(nm)
            if verified:
                dot = QLabel("●")
                dot.setStyleSheet("color: #3373F7; font-size: 12px;")
                dot.setToolTip("Проверено вживую")
                nh.addWidget(dot)
            nh.addStretch(1)
            v.addLayout(nh)
            ds = QLabel(descr)
            ds.setObjectName("muted")
            ds.setWordWrap(True)
            v.addWidget(ds)
            ft = QLabel("остальное — через VPN" if gproxy else "остальное — напрямую")
            ft.setObjectName("hint")
            v.addWidget(ft)
            act = QLabel("● АКТИВЕН")
            act.setObjectName("activeTag")
            act.setVisible(False)
            v.addWidget(act)
            hl.addLayout(v, 1)
            info_btn = QPushButton(">")
            info_btn.setFixedSize(30, 30)
            info_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            info_btn.clicked.connect(lambda _=False, p=pid: self.preset_details(p))
            hl.addWidget(info_btn)
            rb = QLabel()
            rb.setFixedSize(18, 18)
            hl.addWidget(rb)
            self.preset_btns[pid] = (b, rb, act)
            bl.addWidget(b)
        bl.addStretch()

    def on_use_preset(self, checked):
        if not checked:
            if self.active_profile != "default":
                self._last_preset = self.active_profile
                self.select_preset("default")
        else:
            target = getattr(self, "_last_preset", None) or "default"
            if target != self.active_profile:
                self.select_preset(target)

    def preset_details(self, pid):
        meta = next((p for p in PRESETS if p[0] == pid), None)
        if meta is None:
            return
        _, name, icon, descr, verified, gproxy, direct, proxy, _block = meta
        dlg = QDialog(self)
        dlg.setWindowTitle(name)
        lay = QVBoxLayout(dlg)
        t = QLabel("%s %s" % (icon, name))
        t.setObjectName("h2")
        lay.addWidget(t)
        d = QLabel(descr)
        d.setObjectName("muted")
        d.setWordWrap(True)
        lay.addWidget(d)
        f = QLabel("остальное — " + ("через VPN" if gproxy else "напрямую"))
        f.setObjectName("hint")
        lay.addWidget(f)
        c = QLabel(preset_summary(direct, proxy))
        c.setObjectName("hint")
        c.setWordWrap(True)
        lay.addWidget(c)
        if pid == self.active_profile:
            live = []
            for _dom, _exp in CANARIES.get(pid, []):
                _got, _ = route_lookup(_dom)
                _want = "VPN" if _exp == "proxy" else "напрямую"
                if _got == _exp:
                    live.append("%s → %s ✓" % (_dom, _want))
                elif _got == "?":
                    live.append("%s → %s …" % (_dom, _want))
                else:
                    live.append("%s → %s ✗ сейчас %s"
                                % (_dom, _want, "VPN" if _got == "proxy" else "напрямую"))
        else:
            live = ["%s → %s (когда применишь)" % (_dom, "VPN" if _exp == "proxy" else "напрямую")
                    for _dom, _exp in CANARIES.get(pid, [])]
        if live:
            lv = QLabel("\n".join(live))
            lv.setObjectName("hint")
            lv.setWordWrap(True)
            lay.addWidget(lv)
        v = QLabel(("✓ проверено вживую" if verified else "○ ещё не проверялось")
                   + (" · АКТИВЕН" if pid == self.active_profile else ""))
        v.setObjectName("muted")
        lay.addWidget(v)
        row = QHBoxLayout()
        if pid != self.active_profile:
            ap = QPushButton("Применить")
            ap.clicked.connect(lambda: (self.select_preset(pid), dlg.accept()))
            row.addWidget(ap)
        cl = QPushButton("Закрыть")
        cl.clicked.connect(dlg.accept)
        row.addWidget(cl)
        lay.addLayout(row)
        dlg.exec()

    def select_preset(self, pid):
        cur = self.active_profile
        if pid == cur:
            return
        w = CmdWorker(host_cmd("neodon-hostctl profile %s" % pid), 15)
        w.ok.connect(lambda _out, p=pid: self._preset_ok(p))
        w.fail.connect(lambda err: self.statusBar().showMessage("Ошибка профиля: %s" % err, 6000))
        w.start()
        self._workers.append(w)

    def _preset_ok(self, pid):
        self.active_profile = pid
        self.render_presets()
        self.poll_status()

    def render_presets(self):
        for pid, (_b, rb, act) in self.preset_btns.items():
            checked = pid == self.active_profile
            rb.setPixmap(icon_pixmap("check" if checked else "dots", 16,
                                     "#4ADE80" if checked else "#33333D"))
            act.setVisible(checked)
            _b.setObjectName("rowCardActive" if checked else "rowCard")
            _b.style().unpolish(_b)
            _b.style().polish(_b)
        if getattr(self, "use_preset_cb", None) is not None:
            try:
                self.use_preset_cb.blockSignals(True)
                self.use_preset_cb.setChecked(self.active_profile != "default")
            finally:
                self.use_preset_cb.blockSignals(False)

    # ---- Settings ----
    def _build_settings(self):
        w, bl = self._page("Settings")
        self.stack.addWidget(w)
        self.pages["settings"] = w

        sc, sl = self._card(bl, "SUBSCRIPTION")
        url, _, _ = converter_consts()
        self.sub_url = QLineEdit(url or "")
        self.sub_url.setReadOnly(True)
        sl.addWidget(self.sub_url)
        srow = QHBoxLayout()
        self.sub_updated = QLabel("Обновлено: —")
        self.sub_updated.setObjectName("muted")
        ref = QPushButton("Обновить подписку")
        ref.setObjectName("accent")
        ref.clicked.connect(self.refresh_sub)
        self._refresh_btns = getattr(self, "_refresh_btns", []) + [ref]
        srow.addWidget(self.sub_updated)
        srow.addStretch()
        srow.addWidget(ref)
        sl.addLayout(srow)

        gc, gl = self._card(bl, "GENERAL")
        auto = QLabel("VPN запускается системным сервисом автоматически.")
        auto.setObjectName("muted")
        auto.setWordWrap(True)
        gl.addWidget(auto)
        dns_row = QHBoxLayout()
        dns_l = QLabel("DNS")
        dns_l.setObjectName("muted")
        self.dns_edit = QLineEdit("1.1.1.1")
        dns_row.addWidget(dns_l)
        dns_row.addWidget(self.dns_edit, 1)
        gl.addLayout(dns_row)

        g2, g2l = self._card(bl, "APP ROUTING")
        desc = QLabel("Приложения, которые ходят напрямую (в обход VPN) в PROXY-режиме.")
        desc.setObjectName("muted")
        desc.setWordWrap(True)
        g2l.addWidget(desc)
        btn = QPushButton("Настроить приложения")
        btn.setObjectName("accent")
        btn.clicked.connect(lambda: self.navigate("apps"))
        g2l.addWidget(btn)

        bl.addStretch()

    # ---- Logs ----
    def _build_logs(self):
        w, bl = self._page("Logs", scrollable=False)
        self.stack.addWidget(w)
        self.pages["logs"] = w
        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setMaximumBlockCount(2000)
        bl.addWidget(self.log_view, 1)
        lrow = QHBoxLayout()
        clr = QPushButton("Очистить")
        clr.setObjectName("ghost")
        clr.clicked.connect(lambda: self.log_view.clear())
        ref = QPushButton("Обновить")
        ref.setObjectName("accent")
        ref.clicked.connect(self.refresh_logs)
        lrow.addStretch()
        lrow.addWidget(clr)
        lrow.addWidget(ref)
        bl.addLayout(lrow)

    def refresh_logs(self):
        if SANDBOX:
            cmd = host_cmd("journalctl --user -u sing-box.service -u sing-box-full.service -u sing-box-proxy.service -n 300 --no-pager")
        else:
            cmd = "journalctl --user -u sing-box.service -u sing-box-full.service -u sing-box-proxy.service -n 300 --no-pager"
        w = CmdWorker(cmd, 12)
        w.ok.connect(lambda out: self.log_view.setPlainText(out))
        w.fail.connect(lambda _: None)
        w.start()
        self._workers.append(w)

    # ---- Apps (V1 AppsDialog, встроенный) ----
    def _build_apps(self):
        w, bl = self._page("Маршрутизация приложений")
        self.stack.addWidget(w)
        self.pages["apps"] = w
        hint = QLabel("Отметьте приложения, которые должны ходить напрямую (в обход VPN).")
        hint.setObjectName("muted")
        bl.addWidget(hint)
        self.apps_scroll = QScrollArea()
        self.apps_scroll.setWidgetResizable(True)
        self.apps_scroll.setFrameShape(QFrame.Shape.NoFrame)
        _enable_kinetic(self.apps_scroll)
        self.apps_cont = QWidget()
        self.apps_rows = QVBoxLayout(self.apps_cont)
        self.apps_rows.setContentsMargins(4, 4, 4, 4)
        self.apps_scroll.setWidget(self.apps_cont)
        bl.addWidget(self.apps_scroll, 1)
        self.apps_done = QPushButton("Применить")
        self.apps_done.setObjectName("accent")
        bl.addWidget(self.apps_done)
        self._apps_loaded = False
        self.apps_page = _AppsPage(self)

    # ---- About ----
    def _build_about(self):
        w, bl = self._page("О программе")
        self.stack.addWidget(w)
        self.pages["about"] = w
        t = QLabel("Neodon VPN")
        t.setObjectName("h1")
        t.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bl.addWidget(t)
        v = QLabel("V2 — клон v2RayTun для Linux (Bazzite)")
        v.setObjectName("muted")
        v.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bl.addWidget(v)
        e = QLabel("sing-box engine · PySide6 GUI · правила сообщества из v2RayTun")
        e.setObjectName("muted")
        e.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bl.addWidget(e)
        bl.addStretch()

    # ---- режимы/статус ----
    def set_mode(self, mode, restart=False):
        changed = mode != self.mode
        self.mode = mode
        self.btn_proxy.setChecked(mode == "smart")
        self.btn_tunnel.setChecked(mode == "full")
        for b, on_mode in ((self.btn_proxy, "smart"), (self.btn_tunnel, "full")):
            b.setObjectName("modeOn" if mode == on_mode else "modeOff")
            b.style().unpolish(b)
            b.style().polish(b)
        if restart and changed and (self.connected or self.state not in ("OFF", "STOPPING")):
            self._request_op("toggle", mode)
        elif mode in ("smart", "full"):
            self.desired = mode
            self.write_gui_state()

    def _mode_label(self, mode):
        return self.MODE_LABELS.get(mode or "", (mode or "?").upper())

    def _apply_power_icon(self):
        from PySide6.QtGui import QIcon
        self.power.setIcon(QIcon(icon_pixmap("power", self.power.iconSize().width(), "#F5F5F7")))

    def on_power(self):
        try:
            if time.monotonic() < getattr(self, "_settle_until", 0):
                # double-tap guard: a tap landing right after OFF would
                # re-enable the VPN and look like "off didn't work"
                self.statusBar().showMessage("Операция только завершилась — подождите…", 3000)
                return
        except RuntimeError:
            pass
        if self.connected or self.state in ("LOCKED", "FAILED", "DEGRADED"):
            self._request_op("toggle", "off")
        else:
            self._request_op("toggle", self.mode)

    def _request_op(self, kind, *args):
        """Single funnel for user ops: run now, or queue last-wins while busy
        (a dropped off-press during a switch looked like 'off is broken')."""
        if self._op_in_progress:
            self._pending = (kind, args)
            self.statusBar().showMessage("Операция уже выполняется — поставлю в очередь…", 4000)
            return
        self._run_op(kind, *args)

    def _run_op(self, kind, *args):
        if kind == "toggle":
            self.toggle(*args)
        elif kind == "server":
            self._start_server_worker(*args)

    def _drain_pending(self):
        pend, self._pending = self._pending, None
        if pend:
            self._run_op(pend[0], *pend[1])

    def toggle(self, mode):
        if self._op_in_progress:
            self.statusBar().showMessage("Операция уже выполняется — подождите…", 4000)
            return
        self._op_in_progress = True
        self._fast_poll_until = time.monotonic() + 12
        try:
            self.set_state("TRANSITIONING")
        except RuntimeError:
            pass
        w = ToggleWorker(mode)
        w.done.connect(self._toggle_done)
        w.start()
        self._workers.append(w)

    def _toggle_done(self, ok, out):
        self._op_in_progress = False
        self._settle_until = time.monotonic() + 5
        self.statusBar().showMessage(out or ("Готово" if ok else "Ошибка"), 6000)
        self.poll_status()
        self._drain_pending()

    def _log_transition(self, old, new):
        try:
            tr = getattr(self, "_transitions", None)
            if tr is None:
                tr = self._transitions = []
            tr.append((int(time.time()), old, new))
            del tr[:-50]
        except Exception:
            pass

    def _journal_transition(self, old, new, d):
        """Persistent transition log: proves real reconnects vs pill flaps."""
        try:
            p = os.path.join(STATE_DIR, "transitions.log")
            if os.path.exists(p) and os.path.getsize(p) > 20000:
                with open(p) as f:
                    tail = f.readlines()[-150:]
                with open(p, "w") as f:
                    f.writelines(tail)
            with open(p, "a") as f:
                f.write("%d %s->%s desired=%s exit=%s\n"
                        % (int(time.time()), old, new,
                           (d or {}).get("desired_mode") or "?",
                           (d or {}).get("exit_ip") or "-"))
        except OSError:
            pass

    def set_state(self, s):
        """Single state entry: binds timer epoch, buttons, tray to one state."""
        s = (s or "OFF").upper()
        old = getattr(self, "state", None)
        if old != s:
            self._log_transition(old, s)
        self.state = s
        if s == "CONNECTED":
            if getattr(self, "_epoch", None) is None:
                self._epoch = time.monotonic()
        else:
            self._epoch = None
            try:
                self.timer_lbl.setText("00:00:00")
            except RuntimeError:
                pass
        try:
            self.render_status()
        except RuntimeError:
            pass
        self._sync_tray(s)

    def _sync_tray(self, s):
        tray = getattr(self, "tray", None)
        if tray is None:
            return
        try:
            srv = ""
            d = getattr(self, "status", None) or {}
            tag = d.get("server_tag") or ""
            if tag:
                srv = " · " + tag.split("]")[-1].strip()[:24]
            human = {"CONNECTED": "ON", "TRANSITIONING": "переход…",
                     "STARTING": "переход…", "CONNECTING": "переход…",
                     "STOPPING": "переход…"}.get(s, s)
            mode = self.MODE_LABELS.get(getattr(self, "mode", ""), "") or ""
            me = (" · " + mode) if mode and s == "CONNECTED" else ""
            tray.setToolTip("Neodon VPN — %s%s%s" % (human, me, srv))
            icon_kind = "theme"
            if s == "CONNECTED":
                # flag of the active server instead of a generic dot
                fpix = flag_pixmap(flag_code(tag), 22, 15) if tag else None
                if fpix is not None and not fpix.isNull():
                    tray.setIcon(QIcon(fpix))
                    icon_kind = "flag"
            if icon_kind == "theme":
                names = {"CONNECTED": "network-vpn-connected",
                         "LOCKED": "network-vpn-acquiring",
                         "FAILED": "network-error"}
                if s in names and QIcon.hasThemeIcon(names[s]):
                    tray.setIcon(QIcon.fromTheme(names[s]))
            try:
                with open(os.path.join(STATE_DIR, "tray-state.json"), "w") as _f:
                    _f.write(json.dumps({"state": s, "tooltip": "Neodon VPN — %s%s%s" % (human, me, srv),
                                         "icon": icon_kind, "ts": int(time.time())}))
            except OSError:
                pass
        except Exception:
            pass

    def tick(self):
        try:
            if os.path.exists(ACTION_HOOK):
                try:
                    with open(ACTION_HOOK) as _f:
                        hook = json.load(_f)
                except (OSError, ValueError):
                    hook = {}
                os.remove(ACTION_HOOK)
                if isinstance(hook, dict) and hook.get("action") == "navigate":
                    self.navigate(hook.get("page") or "home")
                elif isinstance(hook, dict) and hook.get("action") == "grab":
                    try:
                        self.grab().save(os.path.expanduser(
                            hook.get("path") or "~/neodon-grab.png"))
                    except RuntimeError:
                        pass
                elif isinstance(hook, dict) and hook.get("action") == "refresh":
                    self.refresh_sub()
                elif isinstance(hook, dict) and hook.get("action") == "scroll":
                    # QA backdoor: scroll current page without synthetic touch
                    try:
                        area = self.stack.currentWidget().findChild(QScrollArea)
                        if area is not None:
                            sb = area.verticalScrollBar()
                            sb.setValue(sb.value() + int(hook.get("by") or 300))
                    except (OSError, RuntimeError, ValueError, TypeError):
                        pass
                else:
                    self._tray_show()
        except (OSError, RuntimeError):
            pass
        ep = getattr(self, "_epoch", None)
        if ep:
            s = max(0, int(time.monotonic() - ep))
            self.timer_lbl.setText("%02d:%02d:%02d" % (s // 3600, (s // 60) % 60, s % 60))

    def _prune_workers(self):
        alive = []
        for w in getattr(self, "_workers", []):
            try:
                if w.isRunning():
                    alive.append(w)
            except (RuntimeError, AttributeError):
                pass
        self._workers = alive

    def poll_status(self):
        self._prune_workers()
        if self._poll_busy:
            self._poll_skipped = getattr(self, "_poll_skipped", 0) + 1
            return
        self._poll_busy = True
        w = CmdWorker(host_cmd("neodon-hostctl status") if SANDBOX else "bash %s status-json" % TOGGLE, 10)
        w.ok.connect(self._status_loaded)
        w.fail.connect(self._status_failed)
        w.start()
        self._workers.append(w)

    def _status_loaded(self, out):
        self._poll_busy = False
        try:
            d = json.loads(out)
        except ValueError:
            self.statusBar().showMessage("Не удалось прочитать статус бэкенда", 5000)
            return
        if not isinstance(d, dict):
            return
        self.status = d
        prof = d.get("profile", "default")
        if prof and prof != self.active_profile and prof in self.preset_btns:
            self.active_profile = prof
            self.render_presets()
        _raw = (d.get("actual_state") or "OFF").upper()
        _cur = getattr(self, "state", None)
        _desired_now = d.get("desired_mode")
        if _raw == "CONNECTED":
            self._off_streak = 0
            _new = "CONNECTED"
        elif (_cur == "CONNECTED"
                and _raw in ("CONNECTING", "DEGRADED", "STARTING", "TRANSITIONING")
                and _desired_now == getattr(self, "_last_desired", _desired_now)):
            # wobble guard: one slow curl must not flap the pill/timer;
            # user switching modes (desired changed) bypasses immediately
            self._off_streak = getattr(self, "_off_streak", 0) + 1
            _new = "CONNECTED" if self._off_streak < 3 else _raw
        else:
            self._off_streak = getattr(self, "_off_streak", 0) + 1
            _new = _raw
        self._last_desired = _desired_now
        if _new != _cur:
            self._log_transition(_cur, _new)
            self._journal_transition(_cur, _new, d)
        try:
            if _fast_poll_wanted(_new, getattr(self, "_fast_poll_until", 0), time.monotonic()):
                QTimer.singleShot(1500, self.poll_status)
        except RuntimeError:
            pass
        self.state = _new
        self.connected = d.get("actual_state") == "CONNECTED"
        if self.state == "CONNECTED":
            if getattr(self, "_epoch", None) is None:
                self._epoch = time.monotonic()
        else:
            # streak already counted above; timer clears only at 3 misses
            if self._off_streak >= 3:
                self._epoch = None
        dm = d.get("desired_mode")
        self.desired = "full" if dm == "full" else "smart"
        if self.state == "OFF":
            try:
                with open(os.path.join(STATE_DIR, "gui-state.json")) as f:
                    saved = json.load(f).get("desired")
                if saved in ("full", "smart"):
                    self.desired = saved
            except (OSError, ValueError):
                pass
        if self.state in ("OFF", "FAILED", "DEGRADED", "LOCKED"):
            pass
        if not self._op_in_progress:
            # polls must not re-highlight mid-toggle: backend .mode still
            # shows the old mode during teardown, flipping buttons back
            self.set_mode(self.desired if self.desired in ("smart", "full") else "smart")
        self.render_status()
        try:
            self._sync_tray(_new)
        except RuntimeError:
            pass
        self.write_gui_state()

    def _status_failed(self, _err):
        self._poll_busy = False
        if not self.status:
            self.state = "OFF"
            self.render_status()

    def render_status(self):
        st = self.state
        d = self.status
        self.pill.set_state(st)
        self.power.setChecked(st == "CONNECTED")
        if st == "CONNECTED":
            tag = d.get("server_tag") or ""
            ip = d.get("exit_ip") or "—"
            lat = d.get("latency_ms")
            self.state_meta.setText("%s\nIP: %s · %s мс" % (tag, ip, lat if lat is not None else "—"))
            self.timer_lbl.setText(self.timer_lbl.text() or "00:00:00")
        elif st == "LOCKED":
            self.state_meta.setText("Трафик заблокирован намеренно: VPN недоступен, firewall активен.")
        elif st == "FAILED":
            self.state_meta.setText("Не удалось подключиться. Нажмите кнопку питания для повтора.")
        elif st == "DEGRADED":
            self.state_meta.setText("Переключение...")
        else:
            self.state_meta.setText("")
            self.timer_lbl.setText("00:00:00")

    def _save_geom(self):
        try:
            p = os.path.join(STATE_DIR, "gui-state.json")
            try:
                with open(p) as f:
                    st = json.load(f)
            except (OSError, ValueError):
                st = {}
            st["geom"] = bytes(self.saveGeometry()).hex()
            with open(p + ".tmp", "w") as f:
                json.dump(st, f)
            os.replace(p + ".tmp", p)
        except (OSError, RuntimeError):
            pass

    def _restore_geom(self):
        try:
            with open(os.path.join(STATE_DIR, "gui-state.json")) as f:
                g = json.load(f).get("geom")
            if g:
                self.restoreGeometry(bytes.fromhex(g))
        except (OSError, ValueError, RuntimeError):
            pass

    def write_gui_state(self):
        path = os.path.join(STATE_DIR, "gui-state.json")
        try:
            try:
                with open(path) as f:
                    st = json.load(f)
            except (OSError, ValueError):
                st = {}
            st.update({"state": self.state, "desired": self.desired,
                       "ts": int(time.time())})
            with open(path + ".tmp", "w") as f:
                json.dump(st, f)
            os.replace(path + ".tmp", path)
        except OSError:
            pass

    # ---- серверы ----
    def reload_servers(self):
        self.servers = load_servers()
        self.lats = {}
        self.render_servers()

    def refresh_active_server(self):
        self.active_addr = None
        try:
            cfg_path = os.path.expanduser("~/AI/singbox/config.json")
            d = json.load(open(cfg_path))
            for o in d.get("outbounds") or []:
                if o.get("tag") == "proxy" and o.get("server"):
                    self.active_addr = o["server"]
                    break
        except (OSError, ValueError):
            pass

    def render_servers(self):
        # clear grid
        self._srv_lat = {}
        while self.srv_grid.count():
            child = self.srv_grid.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        COLS = 2
        for i, s in enumerate(self.servers):
            remark = s.get("remarks") or s.get("address") or ("Сервер %d" % (i + 1))
            code = flag_code(remark)
            row = _ClickFrame(lambda e=None, p=i: self._select_server_idx(p))
            row.setObjectName("serverCard")
            row.setCursor(Qt.CursorShape.PointingHandCursor)
            hl = QHBoxLayout(row)
            hl.setContentsMargins(10, 8, 10, 8)
            hl.setSpacing(10)
            fl = QLabel()
            pix = flag_pixmap(code)
            if pix is not None:
                fl.setPixmap(pix)
            else:
                fl.setText("●")
                fl.setStyleSheet("color:#33333D; font-size:14px;")
            fl.setFixedWidth(36)
            hl.addWidget(fl)
            head = re.sub(r"^\[[A-Za-z0-9]{2,4}\]\s*", "", strip_flags(remark).strip()) or ("Сервер %d" % (i + 1))
            active = bool(self.active_addr) and s.get("address") == self.active_addr
            if active:
                head += "  ●"
            txv = QVBoxLayout()
            txv.setContentsMargins(0, 0, 0, 0)
            txv.setSpacing(0)
            head_lbl = _ElidedLabel(head)
            txv.addWidget(head_lbl)
            desc_lbl = QLabel(server_desc(s))
            desc_lbl.setObjectName("muted")
            txv.addWidget(desc_lbl)
            hl.addLayout(txv, 1)
            lat_lbl = QLabel()
            lat_lbl.setFixedWidth(64)
            lat_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            hl.addWidget(lat_lbl)
            self._srv_lat[i] = lat_lbl
            self._paint_lat(i)
            r = i // COLS
            c = i % COLS
            self.srv_grid.addWidget(row, r, c)
            if active:
                row.setStyleSheet("QFrame#serverCard { background:#14251E; border:1px solid #1A4A2E; border-radius:10px; }")
            else:
                row.setStyleSheet("QFrame#serverCard { background:#1C1C22; border:1px solid #26262E; border-radius:10px; }")

    def _paint_lat(self, i):
        lbl = getattr(self, "_srv_lat", {}).get(i)
        if lbl is None:
            return
        ms = self.lats.get(i)
        if ms is not None and ms >= 0:
            color = "#4ADE80" if ms < 120 else ("#F5A623" if ms < 300 else "#E5484D")
            lbl.setText('<span style="color:%s">%d мс</span>' % (color, ms))
        elif ms == -1:
            lbl.setText('<span style="color:#E5484D">✗</span>')
        else:
            lbl.setText("—")

    def _on_ping_result(self, i, ms):
        self.lats[i] = ms
        self._paint_lat(i)

    def start_ping(self):
        if not self.servers:
            return
        self._ping_glow(True)
        w = PingWorker(self.servers)
        w.result.connect(self._on_ping_result)
        w.done.connect(self._ping_done)
        w.start()
        self._workers.append(w)

    def _ping_glow(self, on):
        try:
            self.sub_ping_btn.setStyleSheet(
                "border: 2px solid #3373F7;" if on else "")
        except RuntimeError:
            pass

    def _ping_done(self):
        self._ping_glow(False)  # latencies already painted in place

    def _select_server_idx(self, idx):
        if not (0 <= idx < len(self.servers)):
            self.statusBar().showMessage("Неверный сервер", 5000)
            return
        self._request_op("server", idx)

    def _start_server_worker(self, idx):
        start_after = self.state != "CONNECTED"
        mode = self.desired if self.desired in ("full", "smart") else "smart"
        self._op_in_progress = True
        self.pill.set_state("TRANSITIONING")
        w = SelectWorker(idx, start_after=start_after, mode=mode)
        w.done.connect(self._select_done)
        try:
            w.phase.connect(lambda s: self.statusBar().showMessage(s, 4000))
        except RuntimeError:
            pass
        w.start()
        self._workers.append(w)

    def select_server(self):
        # legacy QListWidget removed — grid uses direct _select_server_idx on card click
        # keep btn compat: pick active or 0
        if self._op_in_progress:
            self.statusBar().showMessage("Операция уже выполняется — подождите…", 4000)
            return
        if not self.servers:
            self.statusBar().showMessage("Нет серверов", 5000)
            return
        idx = 0
        if self.active_addr:
            for j, _s in enumerate(self.servers):
                if _s.get("address") == self.active_addr:
                    idx = j
                    break
        self._request_op("server", idx)

    def _select_done(self, ok, out):
        self._op_in_progress = False
        self._settle_until = time.monotonic() + 5
        if ok:
            self.statusBar().showMessage("Сервер переключён", 4000)
            self.refresh_active_server()
            self.render_servers()
        else:
            self.statusBar().showMessage("Ошибка: %s" % (out or "?"), 8000)
            self.pill.set_state(self.state or "OFF")
        self.poll_status()
        self._drain_pending()

    def status_meta_ip(self, ip):
        # exit ip уже приходит в status-json; здесь дублируем для информации
        pass

    # ---- подписка ----
    def _sub_script(self, fetch_body):
        url, _, raw = converter_consts()
        if not url:
            return None, url
        script = ("curl -sL -A 'v2rayN/7.24.6' -c /tmp/neodon_cj.txt -o /dev/null -m 15 '%s' >/dev/null 2>&1 || true\n"
                  "curl -sL -A 'v2rayN/7.24.6' -b /tmp/neodon_cj.txt -D /tmp/neodon_hdr.txt -o /dev/null -m 15 '%s' >/dev/null 2>&1 || true\n"
                  "grep -i '^subscription-userinfo:' /tmp/neodon_hdr.txt | tr -d '\\r' || true\n" % (url, url))
        if fetch_body:
            script += (
                "curl -sL -A 'v2rayN/7.24.6' -b /tmp/neodon_cj.txt -m 15 '%s' -o /tmp/neodon_body.json || exit 2\n"
                "python3 -c \"import json;d=json.load(open('/tmp/neodon_body.json'));"
                "assert isinstance(d,list) and d and 'outbounds' in d[0]\" || exit 3\n"
                "mv /tmp/neodon_body.json '%s' || exit 4\n" % (url, raw))
        script += "echo DONE\n"
        return script, url

    def fetch_sub_info(self):
        script, url = self._sub_script(fetch_body=False)
        if not script:
            return
        w = CmdWorker(script, 20)
        w.ok.connect(self._sub_loaded)
        w.fail.connect(lambda _: self._sub_clear())
        w.start()
        self._workers.append(w)

    def refresh_sub(self):
        script, url = self._sub_script(fetch_body=True)
        if not script:
            self.statusBar().showMessage("URL подписки не найден", 6000)
            return
        self.statusBar().showMessage("Обновление подписки…")
        for b in getattr(self, "_refresh_btns", []):
            try:
                b.setEnabled(False)
            except RuntimeError:
                pass
        try:
            self.sub_updated.setText("Обновление…")
        except RuntimeError:
            pass
        w = CmdWorker(script, 45)
        w.ok.connect(self._sub_loaded_full)
        w.fail.connect(self._sub_failed)
        w.start()
        self._workers.append(w)
        self._spin_start()

    def _spin_start(self):
        if getattr(self, "_spin_timer", None) is not None:
            return
        self._spin_angle = 0
        self._spin_phase = "run"
        self._spin_rest = self.sub_refresh_btn.icon()
        # hires base: rotating a tiny pixmap crawls (shimmer); downscale hides it
        self._spin_base = icon_pixmap("refresh", 48, "#3373F7")
        for b in getattr(self, "_refresh_btns", []):
            try:
                b.setStyleSheet("border: 2px solid #3373F7;")
            except RuntimeError:
                pass
        t = QTimer(self)
        t.setInterval(50)
        t.timeout.connect(self._spin_tick)
        self._spin_timer = t
        t.start()

    def _spin_tick(self):
        try:
            self._spin_angle = getattr(self, "_spin_angle", 0) + 15
            if getattr(self, "_spin_phase", "run") == "settle" \
                    and self._spin_angle % 360 == 0:
                self._spin_finish()
                return
            base = getattr(self, "_spin_base", None)
            if base is None:
                return
            # fixed canvas: rotating the pixmap itself changes its bounding
            # box (pulse back-and-forth); rotate the painter instead
            from PySide6.QtGui import QPainter, QPixmap
            canvas = QPixmap(68, 68)
            canvas.fill(Qt.GlobalColor.transparent)
            p = QPainter(canvas)
            p.setRenderHints(QPainter.RenderHint.Antialiasing
                             | QPainter.RenderHint.SmoothPixmapTransform)
            p.translate(34, 34)
            p.rotate(self._spin_angle % 360)
            p.drawPixmap(-base.width() // 2, -base.height() // 2, base)
            p.end()
            self.sub_refresh_btn.setIcon(QIcon(canvas))
        except RuntimeError:
            pass

    def _spin_stop(self):
        if getattr(self, "_spin_timer", None) is None:
            return
        self._spin_phase = "settle"
        try:
            self._spin_timer.setInterval(25)
        except RuntimeError:
            pass

    def _spin_finish(self):
        try:
            self._spin_timer.stop()
        except (RuntimeError, AttributeError):
            pass
        self._spin_timer = None
        self._spin_phase = "run"
        self._spin_angle = 0
        try:
            rest = getattr(self, "_spin_rest", None)
            if rest is not None:
                self.sub_refresh_btn.setIcon(rest)
        except (RuntimeError, AttributeError):
            pass
        for b in getattr(self, "_refresh_btns", []):
            try:
                b.setEnabled(True)
                b.setStyleSheet("")
            except RuntimeError:
                pass

    def _refresh_restore(self):
        self._spin_stop()

    def _sub_failed(self, err):
        self._refresh_restore()
        self.statusBar().showMessage(
            "Ошибка подписки: " + (err[-120:] if err else "?"), 8000)

    def _sub_clear(self):
        self.sub_progress.setValue(0)
        self.sub_used.setText("N/A")
        self.sub_expire.setText(sub_expire(None))

    def _sub_cache_or_reason(self, out, line):
        if not (out or "").strip():
            reason = "Нет ответа сети"
        elif not line:
            reason = "Нет userinfo в ответе"
        else:
            reason = "Пустая квота (total=0)"
        try:
            with open(os.path.join(STATE_DIR, "sub-cache.json")) as f:
                c = json.load(f)
            return reason, (c.get("pct", 0), c.get("used", ""), c.get("expire", ""))
        except (OSError, ValueError):
            return reason, None

    def _apply_sub_info(self, out):
        line = next((l for l in (out or "").splitlines() if "subscription-userinfo" in l.lower()), "")
        info = parse_sub_info(line)
        used, total = sub_used_total(info)
        if total > 0:
            self.sub_progress.setValue(sub_used_pct(info))
            self.sub_used.setText(sub_summary(info))
            try:
                with open(os.path.join(STATE_DIR, "sub-cache.json"), "w") as f:
                    json.dump({"pct": sub_used_pct(info), "used": sub_summary(info),
                               "expire": sub_expire(info), "ts": int(time.time())}, f)
            except OSError:
                pass
        else:
            reason, cached = self._sub_cache_or_reason(out, line)
            if cached:
                self.sub_progress.setValue(cached[0])
                self.sub_used.setText(cached[1] + " (кэш)")
                self.sub_expire.setText(cached[2])
            else:
                self.sub_progress.setValue(0)
                self.sub_used.setText("N/A")
            self.statusBar().showMessage(reason, 6000)
            return
        self.sub_expire.setText(sub_expire(info))

    def _sub_loaded(self, out):
        self._apply_sub_info(out)

    def _sub_loaded_full(self, out):
        self._refresh_restore()
        self._apply_sub_info(out)
        self.sub_updated.setText("Обновлено: " + time.strftime("%d.%m %H:%M"))
        self.reload_servers()
        self.statusBar().showMessage("Подписка обновлена", 6000)

    def _setup_tray(self):
        try:
            from PySide6.QtWidgets import QSystemTrayIcon, QMenu
            from PySide6.QtGui import QAction, QIcon
        except Exception:
            return
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return
        self.tray = QSystemTrayIcon(self)
        # use same shield svg as icon, fallback to standard
        try:
            icon = QIcon("/home/m26/.local/share/icons/hicolor/scalable/apps/io.neodon.gui.svg")
            if icon.isNull():
                icon = self.windowIcon() or QIcon.fromTheme("network-vpn")
        except Exception:
            icon = self.windowIcon()
        self.tray.setIcon(icon if not icon.isNull() else QIcon.fromTheme("network-vpn"))
        self.tray.setToolTip("Neodon VPN")
        menu = QMenu()
        act_show = menu.addAction("Показать")
        act_show.triggered.connect(self._tray_show)
        menu.addSeparator()
        act_proxy = menu.addAction("PROXY")
        act_proxy.triggered.connect(lambda: self.set_mode("smart", restart=True))
        act_tunnel = menu.addAction("TUNNEL")
        act_tunnel.triggered.connect(lambda: self.set_mode("full", restart=True))
        menu.addSeparator()
        act_quit = menu.addAction("Выход")
        act_quit.triggered.connect(self._tray_quit)
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._tray_activated)
        self.tray.show()
        self._tray_first_hide = True

    def _tray_show(self):
        self.show()
        self.raise_()
        self.activateWindow()

    def _tray_activated(self, reason):
        from PySide6.QtWidgets import QSystemTrayIcon
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self._tray_show()

    def _tray_quit(self):
        self._really_quit = True
        self.close()

    def closeEvent(self, event):
        # minimize to tray instead of quit — like steam/qbit near clock
        try:
            self._save_geom()
        except RuntimeError:
            pass
        if getattr(self, "_really_quit", False):
            for w in list(self._workers):
                try:
                    w.wait(200)
                except RuntimeError:
                    pass
            try:
                super().closeEvent(event)
            except Exception:
                event.accept()
            try:
                if hasattr(self, "tray"):
                    self.tray.hide()
            except Exception:
                pass
            from PySide6.QtWidgets import QApplication as _QA
            _QA.quit()
            return
        if hasattr(self, "tray") and self.tray.isVisible():
            event.ignore()
            self.hide()
            if getattr(self, "_tray_first_hide", False):
                self._tray_first_hide = False
                try:
                    self.tray.showMessage("Neodon VPN", "Скрыт в трей возле часов — клик по иконке чтобы вернуть", QSystemTrayIcon.MessageIcon.Information, 3000)
                except Exception:
                    pass
            return
        # fallback: no tray available — quit as before
        for w in list(self._workers):
            try:
                w.wait(200)
            except RuntimeError:
                pass
        try:
            super().closeEvent(event)
        except Exception:
            event.accept()
        from PySide6.QtWidgets import QApplication as _QA
        _QA.quit()


class _AppsPage(QWidget):
    """Маршрутизация приложений (V1 AppsDialog, как страница)."""

    def __init__(self, win):
        super().__init__()
        self.win = win
        self.checks = {}
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(500)
        self._timer.timeout.connect(self._save_and_apply)
        for cb in _iter_cbs(win.apps_rows):
            cb.toggled.connect(self._schedule)

    def refresh(self):
        try:
            direct = set(json.load(open(RULES_JSON)).get("direct", []))
        except (OSError, ValueError):
            direct = set()
        from PySide6.QtWidgets import QCheckBox
        from PySide6.QtCore import QTimer as _Q
        apps = _list_apps(self.win)
        if self.checks:
            # обновить только состояния
            for proc, cb in self.checks.items():
                cb.setChecked(proc in direct)
            return
        rows = self.win.apps_rows
        while rows.count():
            it = rows.takeAt(0)
            if it.widget():
                it.widget().deleteLater()
        for proc, name in apps:
            cb = QCheckBox("%s   (%s)" % (name, proc))
            cb.setChecked(proc in direct)
            cb.toggled.connect(self._schedule)
            rows.addWidget(cb)
            self.checks[proc] = cb
        rows.addStretch()

    def _schedule(self):
        self._timer.start()

    def _save_and_apply(self):
        direct = sorted(p for p, cb in self.checks.items() if cb.isChecked())
        try:
            with open(RULES_JSON, "w") as f:
                f.write(json.dumps({"direct": direct}, indent=2) + "\n")
        except OSError:
            return
        w = CmdWorker("python3 %s" % HELPER, 30)
        w.ok.connect(lambda out: self.win.statusBar().showMessage(
            "Правила применены: " + (out.splitlines()[-1] if out else "OK"), 6000))
        w.fail.connect(lambda err: self.win.statusBar().showMessage(
            "Ошибка правил: " + (err[-160:] if err else "?"), 8000))
        w.start()
        self.win._workers.append(w)


def _iter_cbs(layout):
    for i in range(layout.count()):
        it = layout.itemAt(i)
        w = it.widget()
        if isinstance(w, QCheckBox):
            yield w


def _list_apps(win):
    apps = {}
    rc, out, _ = run_cmd("flatpak list --app --columns=application,name", timeout=10)
    if rc == 0:
        for line in out.splitlines():
            parts = line.split("\t")
            if len(parts) >= 2 and parts[0].strip():
                app_id, name = parts[0].strip(), parts[1].strip()
                proc = FLATPAK_MAP.get(app_id) or app_id.rsplit(".", 1)[-1].lower()
                apps[proc] = name or app_id
    for base in (os.path.join(HOME, ".local/share/applications"), "/usr/share/applications"):
        try:
            for f in sorted(os.listdir(base)):
                if not f.endswith(".desktop"):
                    continue
                name = exec_line = None
                for line in open(os.path.join(base, f), errors="ignore"):
                    if line.startswith("Name=") and name is None:
                        name = line[5:].strip()
                    elif line.startswith("Exec="):
                        exec_line = line[5:].strip()
                if exec_line:
                    toks = exec_line.split()
                    if toks and toks[0] == "env":
                        toks = [t for t in toks[1:] if "=" not in t]
                    if toks:
                        proc = os.path.basename(toks[0].split("%")[0]).strip()
                        if proc:
                            apps.setdefault(proc, name or proc)
        except OSError:
            pass
    return sorted(apps.items(), key=lambda kv: kv[1].lower())


def main():
    # Single-instance lock: shared writable path used by BOTH the dev copy and
    # the flatpak sandbox (~/.var/app/io.neodon.gui is granted in the sandbox by
    # default). flock освобождается ядром при любой смерти процесса (kill -9),
    # устойчив к PID-переиспользованию — в отличие от QLockFile не застревает.
    lock_dir = os.path.expanduser("~/.var/app/io.neodon.gui")
    try:
        os.makedirs(lock_dir, exist_ok=True)
    except OSError:
        lock_dir = "/tmp"
    lock_path = os.path.join(lock_dir, "neodon-gui.lock")
    try:
        import fcntl
        _LOCK_FD = os.open(lock_path, os.O_CREAT | os.O_RDWR, 0o644)
        try:
            fcntl.flock(_LOCK_FD, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            # Второй экземпляр: просим показать окно через хук и выходим.
            print("Neodon VPN already running", file=sys.stderr)
            try:
                with open(ACTION_HOOK, "w") as _f:
                    _f.write(json.dumps({"action": "show", "ts": int(time.time())}))
            except OSError:
                pass
            return 0
    except ImportError:
        # Fallback без fcntl (не Linux): файл-маркер с проверкой живого PID.
        try:
            with open(lock_path) as f:
                old_pid = int(f.readline().strip())
            with open("/proc/%d/cmdline" % old_pid, "rb") as f:
                if b"neodon-vpn" in f.read():
                    print("Neodon VPN already running", file=sys.stderr)
                    return 0
        except (OSError, ValueError):
            pass
        open(lock_path, "w").write(str(os.getpid()) + "\n")
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(QSS)
    win = MainWindow()
    win.show()
    rc = app.exec()
    return rc


if __name__ == "__main__":
    sys.exit(main())