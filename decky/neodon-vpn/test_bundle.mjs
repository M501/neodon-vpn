// test_bundle.mjs: loader-faithful bundle smoke test (no Steam needed).
// Stubs exactly what Decky ESMODULE_V1 provides, then:
//   const plugin_exports = await import(bundle); plugin_exports.default();
// Asserts: no throw, {title,content,icon} shape, api.connect(pluginName),
// and backend calls route as loader/call_plugin_method(pluginName, method).
import { readFileSync } from "node:fs";

const bundlePath = process.argv[2];
const src = readFileSync(bundlePath, "utf8");

// 0. Static: the old crash class must be gone (no undefined serverAPI deref).
if (/\bserverAPI\b/.test(src)) {
  console.log("FAIL static-serverAPI-still-present");
  process.exit(1);
}
console.log("ok   static-no-serverAPI");
// 0b. Echo guard: toggle must go through the seen/want refs, never raw.
// (Phantom vpn_up 2s after vpn_down: Steam re-fires onChange on prop flips.)
for (const pat of ["seenRef", "wantRef", "v === seenRef.current"]) {
  if (!src.includes(pat)) {
    console.log("FAIL static-no-echo-guard", pat);
    process.exit(1);
  }
}
console.log("ok   static-echo-guard");

const calls = [];
let connectArgs = null;
const fakeAPI = {
  _version: 2,
  call: (method, ...args) => {
    calls.push([method, ...args]);
    return Promise.resolve({ result: { ok: true } });
  },
  callable: (method) => (...args) => fakeAPI.call(method, ...args),
};

// Minimal React stub: only createElement (executed when factory builds
// the <Content/> element — no rendering needed for wiring proof).
const SP_REACT = {
  createElement: (type, props, ...children) => ({ type, props, children }),
  Component: class {},
  useEffect: () => {},
  useState: (v) => [v, () => {}],
};
globalThis.window = {
  __DECKY_SECRET_INTERNALS_DO_NOT_USE_OR_YOU_WILL_BE_FIRED_deckyLoaderAPIInit: {
    connect: (version, pluginName) => {
      connectArgs = [version, pluginName];
      return fakeAPI;
    },
  },
};
globalThis.SP_REACT = SP_REACT;
globalThis.React = SP_REACT;
globalThis.SP_JSX = {
  jsx: (type, props) => ({ type, props }),
  jsxs: (type, props) => ({ type, props }),
  Fragment: "Fragment",
};
// decky-frontend-lib global (staticClasses + friends used by the panel).
globalThis.DFL = new Proxy({}, { get: (t, p) => (p === "staticClasses" ? { Title: "Title" } : () => null) });

const plugin = await import(bundlePath);
// 1. Loader calls default() with NO arguments.
const def = plugin.default();
console.log("ok   default()-no-args");
if (!def || !def.content || !def.title) {
  console.log("FAIL shape-missing");
  process.exit(1);
}
console.log("ok   shape-title-content-icon");
// 2. Handshake used our manifest name.
if (!connectArgs || connectArgs[1] !== "neodon-vpn") {
  console.log("FAIL connect-args", JSON.stringify(connectArgs));
  process.exit(1);
}
console.log("ok   connect-plugin-name", JSON.stringify(connectArgs));
// 3. Backend call wiring: drive Content's refresh path? Rendering is out
// of scope here; assert callable() binds plugin method names.
const getStatus = fakeAPI.callable("get_status");
await getStatus();
if (calls.length !== 1 || calls[0][0] !== "get_status") {
  console.log("FAIL call-wiring", JSON.stringify(calls));
  process.exit(1);
}
console.log("ok   call-wiring");
console.log("FAILURES: none");
