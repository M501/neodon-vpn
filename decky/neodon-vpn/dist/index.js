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
    // Last rendered switch position (echo guard) + last commanded intent.
    // Steam re-fires onChange when a poll flips `checked` mid-transition
    // (off at 1s -> poll still CONNECTED -> checked true -> phantom vpn_up).
    const seenRef = SP_REACT.useRef(false);
    const wantRef = SP_REACT.useRef(null);
    async function refresh() {
        try {
            const st = un(await call("get_status"));
            const ok = !!st?.ok;
            const actual = st?.actual_state || "?";
            const nowOn = ok && actual === "CONNECTED";
            // Quiet window: while our own command is in flight, keep showing the
            // commanded position instead of flapping with half-done backend truth.
            const quiet = wantRef.current !== null && Date.now() - wantRef.current.ts < 8000;
            if (!quiet) {
                setOn(nowOn);
                seenRef.current = nowOn;
            }
            // Honest clock: backend systemd timestamp wins (survives panel
            // reopen); local arming is the fallback. Cleared on drop.
            if (nowOn) {
                const cs = Number(st?.connected_since || 0);
                sinceRef.current = cs > 0 ? cs * 1000 : (sinceRef.current || Date.now());
            }
            else {
                sinceRef.current = 0;
            }
            setOn(nowOn);
            const dm = st?.desired_mode || "smart";
            setMode(dm === "full" ? "full" : "smart");
            const ip = st?.exit_ip || "—";
            setMeta(actual + " · " + ip);
            setRulesName(st?.profile_name || st?.profile || "");
            const sv = un(await call("get_servers"));
            const list = sv?.servers || [];
            const active = sv?.active || "";
            setServers(list.map((s, i) => ({ data: i, label: s.remarks || ("Server " + (i + 1)) })));
            const ai = list.findIndex((s) => s.address && s.address === active);
            // Never snap back to first on a backend hiccup: keep current idx.
            if (ai >= 0)
                setSrvIdx(ai);
            const qq = un(await call("get_quota"))?.quota;
            setQuota(qq && qq.used ? String(qq.used) : "");
        }
        catch (e) {
            setMeta("poll error");
        }
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
        await call(next ? "vpn_up" : "vpn_down");
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
        setSrvIdx(i);
        await call("set_server", i);
        setTimeout(refresh, 1500);
    }
    return (SP_JSX.jsxs(DFL.PanelSection, { title: "Neodon VPN", children: [SP_JSX.jsxs("div", { children: ["Status: ", on ? "● On" : "○ Off", " (", meta, ")"] }), SP_JSX.jsx(DFL.ToggleField, { label: on && sinceRef.current
                    ? "VPN · " + fmtUptime(Math.floor((Date.now() - sinceRef.current) / 1000))
                    : "VPN", checked: on, onChange: (v) => onToggle(v) }), SP_JSX.jsx(DFL.Dropdown, { rgOptions: [
                    { data: "smart", label: "PROXY" },
                    { data: "full", label: "TUNNEL" },
                ], selectedOption: mode, onChange: (v) => switchMode(v?.data || "smart"), strDefaultLabel: "Mode" }), SP_JSX.jsx(DFL.Dropdown, { rgOptions: servers, selectedOption: srvIdx, onChange: (v) => switchServer(Number(v?.data ?? 0)), strDefaultLabel: "Server" }), SP_JSX.jsx(DFL.ButtonItem, { layout: "below", onClick: async () => {
                    setMeta("refreshing subscription…");
                    await call("refresh_sub");
                    refresh();
                }, children: "Refresh (servers + usage)" }), quota !== "" && SP_JSX.jsxs("div", { children: ["Usage: ", quota] }), rulesName !== "" && SP_JSX.jsxs("div", { children: ["Traffic rules: ", rulesName] }), SP_JSX.jsx("div", { children: "* rules come from the desktop app" })] }));
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
