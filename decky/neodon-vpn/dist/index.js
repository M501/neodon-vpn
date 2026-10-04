const manifest = {"name":"neodon-vpn"};
const API_VERSION = 2;
const internalAPIConnection = window.__DECKY_SECRET_INTERNALS_DO_NOT_USE_OR_YOU_WILL_BE_FIRED_deckyLoaderAPIInit;
if (!internalAPIConnection) {
    throw new Error('[@decky/api]: Failed to connect to the loader as as the loader API was not initialized. This is likely a bug in Decky Loader.');
}
let api;
try {
    api = internalAPIConnection.connect(API_VERSION, manifest.name);
}
catch {
    api = internalAPIConnection.connect(1, manifest.name);
    console.warn(`[@decky/api] Requested API version ${API_VERSION} but the running loader only supports version 1. Some features may not work.`);
}
if (api._version != API_VERSION) {
    console.warn(`[@decky/api] Requested API version ${API_VERSION} but the running loader only supports version ${api._version}. Some features may not work.`);
}
const call = api.call;
const definePlugin = (fn) => {
    return (...args) => {
        return fn(...args);
    };
};

var DefaultContext = {
  color: undefined,
  size: undefined,
  className: undefined,
  style: undefined,
  attr: undefined
};
var IconContext = SP_REACT.createContext && /*#__PURE__*/SP_REACT.createContext(DefaultContext);

var _excluded = ["attr", "size", "title"];
function _objectWithoutProperties(e, t) { if (null == e) return {}; var o, r, i = _objectWithoutPropertiesLoose(e, t); if (Object.getOwnPropertySymbols) { var n = Object.getOwnPropertySymbols(e); for (r = 0; r < n.length; r++) o = n[r], -1 === t.indexOf(o) && {}.propertyIsEnumerable.call(e, o) && (i[o] = e[o]); } return i; }
function _objectWithoutPropertiesLoose(r, e) { if (null == r) return {}; var t = {}; for (var n in r) if ({}.hasOwnProperty.call(r, n)) { if (-1 !== e.indexOf(n)) continue; t[n] = r[n]; } return t; }
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
function ownKeys(e, r) { var t = Object.keys(e); if (Object.getOwnPropertySymbols) { var o = Object.getOwnPropertySymbols(e); r && (o = o.filter(function (r) { return Object.getOwnPropertyDescriptor(e, r).enumerable; })), t.push.apply(t, o); } return t; }
function _objectSpread(e) { for (var r = 1; r < arguments.length; r++) { var t = null != arguments[r] ? arguments[r] : {}; r % 2 ? ownKeys(Object(t), true).forEach(function (r) { _defineProperty(e, r, t[r]); }) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(t)) : ownKeys(Object(t)).forEach(function (r) { Object.defineProperty(e, r, Object.getOwnPropertyDescriptor(t, r)); }); } return e; }
function _defineProperty(e, r, t) { return (r = _toPropertyKey(r)) in e ? Object.defineProperty(e, r, { value: t, enumerable: true, configurable: true, writable: true }) : e[r] = t, e; }
function _toPropertyKey(t) { var i = _toPrimitive(t, "string"); return "symbol" == typeof i ? i : i + ""; }
function _toPrimitive(t, r) { if ("object" != typeof t || !t) return t; var e = t[Symbol.toPrimitive]; if (void 0 !== e) { var i = e.call(t, r); if ("object" != typeof i) return i; throw new TypeError("@@toPrimitive must return a primitive value."); } return ("string" === r ? String : Number)(t); }
function Tree2Element(tree) {
  return tree && tree.map((node, i) => /*#__PURE__*/SP_REACT.createElement(node.tag, _objectSpread({
    key: i
  }, node.attr), Tree2Element(node.child)));
}
function GenIcon(data) {
  return props => /*#__PURE__*/SP_REACT.createElement(IconBase, _extends({
    attr: _objectSpread({}, data.attr)
  }, props), Tree2Element(data.child));
}
function IconBase(props) {
  var elem = conf => {
    var attr = props.attr,
      size = props.size,
      title = props.title,
      svgProps = _objectWithoutProperties(props, _excluded);
    var computedSize = size || conf.size || "1em";
    var className;
    if (conf.className) className = conf.className;
    if (props.className) className = (className ? className + " " : "") + props.className;
    return /*#__PURE__*/SP_REACT.createElement("svg", _extends({
      stroke: "currentColor",
      fill: "currentColor",
      strokeWidth: "0"
    }, conf.attr, attr, svgProps, {
      className: className,
      style: _objectSpread(_objectSpread({
        color: props.color || conf.color
      }, conf.style), props.style),
      height: computedSize,
      width: computedSize,
      xmlns: "http://www.w3.org/2000/svg"
    }), title && /*#__PURE__*/SP_REACT.createElement("title", null, title), props.children);
  };
  return IconContext !== undefined ? /*#__PURE__*/SP_REACT.createElement(IconContext.Consumer, null, conf => elem(conf)) : elem(DefaultContext);
}

// THIS FILE IS AUTO GENERATED
function FaShieldAlt (props) {
  return GenIcon({"attr":{"viewBox":"0 0 512 512"},"child":[{"tag":"path","attr":{"d":"M466.5 83.7l-192-80a48.15 48.15 0 0 0-36.9 0l-192 80C27.7 91.1 16 108.6 16 128c0 198.5 114.5 335.7 221.5 380.3 11.8 4.9 25.1 4.9 36.9 0C360.1 472.6 496 349.3 496 128c0-19.4-11.7-36.9-29.5-44.3zM256.1 446.3l-.1-381 175.9 73.3c-3.3 151.4-82.1 261.1-175.8 307.7z"},"child":[]}]})(props);
}

// Loader answers {result: ...} over WS; unwrap defensively (ponytail:
// one line, covers both wrapped and raw shapes).
const un = (r) => r?.result ?? r;
function fmtUptime(sec) {
    const h = Math.floor(sec / 3600);
    const m = Math.floor((sec % 3600) / 60);
    const s = sec % 60;
    const p = (n) => String(n).padStart(2, "0");
    return p(h) + ":" + p(m) + ":" + p(s);
}
// Raw backend states -> human words. The panel must never print FAILED /
// urlopen shapes (owner report 04.10): honest, but calm.
const FRIENDLY = {
    CONNECTED: "connected",
    DEGRADED: "server not responding",
    FAILED: "connection failed",
    STARTING: "starting",
    TRANSITIONING: "switching",
    CONNECTING: "connecting",
    STOPPING: "stopping",
    LOCKED: "killswitch locked",
    OFF: "off",
};
// Short server name for status lines: "🇵🇱 [PL] NEODON…" -> "PL".
function shortLabel(label) {
    const m = /\[([A-Za-z0-9]{1,4})\]/.exec(label || "");
    return m ? m[1] : String(label || "").slice(0, 14);
}
// Classify backend errors into short human text (never dump urlopen guts).
function shortErr(e) {
    const s = String(e || "").replace(/\s+/g, " ");
    if (/429|too many|rate.?limit/i.test(s))
        return "provider rate-limited";
    if (/certificate|CERTIFICATE|ssl|verify failed/i.test(s))
        return "TLS verify failed";
    if (/name resolution|Errno -[235]|getaddrinfo|nodename|Name or service/i.test(s))
        return "no network (DNS)";
    if (/timed? ?out/i.test(s))
        return "timeout";
    if (/urlopen|unreachable|http/i.test(s))
        return "network error";
    return s.slice(0, 48) || "failed";
}
function Content() {
    const [on, setOn] = SP_REACT.useState(false);
    const [mode, setMode] = SP_REACT.useState("smart");
    const [meta, setMeta] = SP_REACT.useState("…");
    const [, setTick] = SP_REACT.useState(0);
    const sinceRef = SP_REACT.useRef(0);
    const [servers, setServers] = SP_REACT.useState([]);
    const [srvIdx, setSrvIdx] = SP_REACT.useState(0);
    const [quota, setQuota] = SP_REACT.useState("");
    const [rulesName, setRulesName] = SP_REACT.useState("");
    const [notice, setNotice] = SP_REACT.useState("");
    const noticeTsRef = SP_REACT.useRef(0);
    // Remount starts false: first paint must say Syncing, never stale OFF.
    const [synced, setSynced] = SP_REACT.useState(false);
    // Last rendered switch position (echo guard) + last commanded intent.
    // Steam re-fires onChange when a poll flips `checked` mid-transition
    // (off at 1s -> poll still CONNECTED -> checked true -> phantom vpn_up).
    const seenRef = SP_REACT.useRef(false);
    const wantRef = SP_REACT.useRef(null);
    // Server dropdown guards (live host showed real ping-pong here: 4/5/5/4/4/5
    // set_server calls per action). seenSrv = last rendered value; progSrvTs =
    // when WE last moved the dropdown (so a same-value re-fire can be told
    // apart from a deliberate re-tap).
    const seenSrvRef = SP_REACT.useRef(-1);
    const progSrvTsRef = SP_REACT.useRef(0);
    // Pending command: shown immediately as "switching to X…"/"connecting…"
    // until backend truth confirms it (or 15 s). Kills the dead 5-s-poll feel.
    const pendRef = SP_REACT.useRef(null);
    // Last observed actual_state (re-tap decisions).
    const stRef = SP_REACT.useRef("");
    function showNotice(s) {
        setNotice(s);
        noticeTsRef.current = Date.now();
    }
    function clearPending() {
        pendRef.current = null;
        setTick((t) => t + 1);
    }
    async function refresh() {
        try {
            // One round trip, not three: panel syncs in ~1 poll, not ~3.
            const [sres, svres, qres] = await Promise.all([
                call("get_status"),
                call("get_servers"),
                call("get_quota"),
            ]);
            const st = un(sres);
            const ok = !!st?.ok;
            const actual = st?.actual_state || "?";
            const dm = st?.desired_mode || "smart";
            stRef.current = actual;
            // Switch follows INTENT (desired_mode), never a transient actual state:
            // mid-transition states must not flip the switch — a prop flip re-fires
            // Steam's onChange and that phantom call restarts or kills the service.
            const nowOn = ok ? dm !== "off" : seenRef.current;
            // Quiet window: while our own power command is in flight, keep showing
            // the commanded position instead of flapping with half-done truth.
            const quiet = wantRef.current !== null && Date.now() - wantRef.current.ts < 8000;
            if (!quiet) {
                setOn(nowOn);
                seenRef.current = nowOn;
            }
            // Honest clock: backend systemd timestamp wins (survives panel reopen);
            // local arming is the fallback. Cleared on drop; never armed mid-fail.
            if (nowOn && actual !== "FAILED" && actual !== "LOCKED") {
                const cs = Number(st?.connected_since || 0);
                sinceRef.current = cs > 0 ? cs * 1000 : (sinceRef.current || Date.now());
            }
            else {
                sinceRef.current = 0;
            }
            setMode(dm === "full" ? "full" : "smart");
            const ip = st?.exit_ip || "";
            const fr = FRIENDLY[actual] || String(actual).toLowerCase();
            const stag = shortLabel(String(st?.server_tag || ""));
            setMeta((stag ? stag + " · " : "") + fr + (ip ? " · " + ip : ""));
            setRulesName(st?.profile_name || st?.profile || "");
            const sv = un(svres);
            const list = sv?.servers || [];
            const active = sv?.active || "";
            setServers(list.map((s, i) => ({ data: i, label: s.remarks || ("Server " + (i + 1)) })));
            const ai = list.findIndex((s) => s.address && s.address === active);
            const p = pendRef.current;
            if (p) {
                // Settle conditions: server pick -> selection persisted AND a settled
                // state (never claim "connected" within the first 3 s — that is the
                // old link still answering; the restart + transition marker follow).
                const settled = p.kind === "srv"
                    ? ai === p.target && (actual === "DEGRADED" || actual === "FAILED" || actual === "LOCKED" ||
                        actual === "OFF" || (actual === "CONNECTED" && Date.now() - p.ts > 3000))
                    : p.kind === "on"
                        ? actual === "CONNECTED" || actual === "DEGRADED" || actual === "FAILED" || actual === "LOCKED"
                        : actual === "OFF";
                if (settled || Date.now() - p.ts > 15000) {
                    call("ui_log", "settle k=" + p.kind + " ai=" + ai + " act=" + actual + " dt=" + (Date.now() - p.ts)).catch(() => { });
                    clearPending();
                }
            }
            // While our set_server is in flight, keep the user's pick rendered:
            // a stale selected-server.json must not flip the dropdown back.
            const srvBusy = pendRef.current?.kind === "srv";
            if (ai >= 0 && !srvBusy) {
                if (ai !== seenSrvRef.current) {
                    call("ui_log", "srvset ai=" + ai + " prev=" + seenSrvRef.current).catch(() => { });
                    progSrvTsRef.current = Date.now();
                }
                setSrvIdx(ai);
                seenSrvRef.current = ai;
            }
            const qq = un(qres)?.quota;
            if (qq && qq.used) {
                let upd = "";
                if (qq.ts) {
                    const d = new Date(Number(qq.ts) * 1000);
                    const p2 = (n) => String(n).padStart(2, "0");
                    upd = " · " + p2(d.getHours()) + ":" + p2(d.getMinutes());
                }
                setQuota(String(qq.used) + upd);
            }
            else {
                setQuota("");
            }
        }
        catch (e) {
            setMeta("backend offline");
        }
        // First paint must never claim OFF: remount starts false, truth arrives late.
        setSynced(true);
    }
    SP_REACT.useEffect(() => {
        refresh();
        const t = setInterval(refresh, 5000);
        const u = setInterval(() => setTick((t) => t + 1), 1000);
        return () => {
            clearInterval(t);
            clearInterval(u);
        };
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);
    async function power(next) {
        wantRef.current = { v: next, ts: Date.now() };
        pendRef.current = { kind: next ? "on" : "off", label: "", target: 0, ts: Date.now() };
        const r = un(await call(next ? "vpn_up" : "vpn_down"));
        if (!r?.ok) {
            clearPending();
            showNotice((next ? "power on" : "power off") + " failed: " + shortErr(r?.out || r?.error));
        }
        setTick((t) => t + 1);
        setTimeout(refresh, 1200);
    }
    function onToggle(v) {
        // No-op echoes (Steam re-firing on a prop flip) must never reach backend.
        if (v === seenRef.current)
            return;
        seenRef.current = v;
        power(v);
    }
    async function switchMode(m) {
        await call("set_mode", m);
        setTimeout(refresh, 1200);
    }
    async function switchServer(i) {
        if (servers.length === 0)
            return;
        if (i === seenSrvRef.current) {
            // Same value re-fire: either a Steam echo right after our own prop
            // change, or a deliberate re-tap of the same server.
            const isEcho = Date.now() - progSrvTsRef.current < 800;
            if (isEcho) {
                call("ui_log", "tap-echo i=" + i).catch(() => { });
                return;
            }
            if (pendRef.current) {
                call("ui_log", "tap-busy i=" + i).catch(() => { });
                return;
            }
            if (stRef.current === "CONNECTED") {
                call("ui_log", "tap-noop i=" + i).catch(() => { });
                return;
            }
            // Deliberate re-tap on a non-connected link: retry (fresh set_server).
        }
        call("ui_log", "tap i=" + i + " prev=" + seenSrvRef.current + " st=" + stRef.current).catch(() => { });
        seenSrvRef.current = i;
        progSrvTsRef.current = Date.now();
        const label = shortLabel(String(servers[i]?.label ?? ""));
        // Instant feedback only when there is a link to switch; with the VPN off
        // picking a server is a silent config change (the dropdown already moved).
        if (stRef.current !== "OFF") {
            pendRef.current = { kind: "srv", label: label, target: i, ts: Date.now() };
        }
        setSrvIdx(i);
        const r = un(await call("set_server", i));
        if (!r?.ok) {
            clearPending();
            showNotice("switch failed: " + shortErr(r?.error || r?.out));
        }
        else {
            call("ui_log", "set-ok i=" + i).catch(() => { });
        }
        setTick((t) => t + 1);
        setTimeout(refresh, 400);
        setTimeout(refresh, 1500);
    }
    const pend = pendRef.current;
    const noticeLive = notice !== "" && Date.now() - noticeTsRef.current < 12000;
    const bad = stRef.current === "DEGRADED" || stRef.current === "FAILED";
    let statusLine;
    if (!synced) {
        statusLine = "Syncing…";
    }
    else if (pend) {
        if (pend.kind === "srv") {
            statusLine = (on ? "● On" : "○ Off") + " (switching to " + pend.label + "…)";
        }
        else if (pend.kind === "on") {
            statusLine = "● On (connecting…)";
        }
        else {
            statusLine = "○ Off (turning off…)";
        }
    }
    else {
        statusLine = (on ? "● On" : "○ Off") + " (" + meta + ")";
    }
    return (SP_JSX.jsxs(DFL.PanelSection, { title: "Neodon VPN", children: [SP_JSX.jsx("div", { children: "Status: " + statusLine }), SP_JSX.jsx(DFL.ToggleField, { label: on && sinceRef.current
                    ? "VPN · " + fmtUptime(Math.floor((Date.now() - sinceRef.current) / 1000))
                    : "VPN", checked: on, onChange: (v) => onToggle(v) }), SP_JSX.jsx(DFL.Dropdown, { rgOptions: [
                    { data: "smart", label: "PROXY" },
                    { data: "full", label: "TUNNEL" },
                ], selectedOption: mode, onChange: (v) => switchMode(v?.data || "smart"), strDefaultLabel: "Mode" }), SP_JSX.jsx(DFL.Dropdown, { rgOptions: servers, selectedOption: srvIdx, onChange: (v) => switchServer(Number(v?.data ?? 0)), strDefaultLabel: "Server" }, "srv-" + srvIdx), !pend && bad && (SP_JSX.jsx("div", { children: "\u21B3 no link \u2014 pick another server, or tap this one again to retry" })), SP_JSX.jsx(DFL.ButtonItem, { layout: "below", onClick: async () => {
                    showNotice("refreshing subscription…");
                    try {
                        const r = un(await call("refresh_sub"));
                        showNotice(r?.ok ? "subscription updated" : "refresh: " + shortErr(r?.error));
                    }
                    catch (e) {
                        showNotice("refresh failed");
                    }
                    setTimeout(refresh, 2500);
                }, children: "Refresh (servers + usage)" }), noticeLive && SP_JSX.jsx("div", { children: notice }), quota !== "" && SP_JSX.jsxs("div", { children: ["Usage: ", quota] }), rulesName !== "" && SP_JSX.jsxs("div", { children: ["Traffic rules: ", rulesName] }), SP_JSX.jsx("div", { children: "* rules come from the desktop app" })] }));
}
var index = definePlugin(() => {
    return {
        title: SP_JSX.jsx("div", { className: DFL.staticClasses.Title, children: "Neodon VPN" }),
        content: SP_JSX.jsx(Content, {}),
        icon: SP_JSX.jsx(FaShieldAlt, {}),
    };
});

export { index as default };
//# sourceMappingURL=index.js.map
