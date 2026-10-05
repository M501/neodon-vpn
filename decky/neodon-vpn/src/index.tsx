import { useEffect, useRef, useState } from "react";
import {
  PanelSection,
  ToggleField,
  Dropdown,
  DropdownOption,
  ButtonItem,
  staticClasses,
} from "@decky/ui";
import { definePlugin, call } from "@decky/api";
import { FaShieldAlt } from "react-icons/fa";

type Mode = "smart" | "full" | "proxy";

// Loader answers {result: ...} over WS; unwrap defensively (ponytail:
// one line, covers both wrapped and raw shapes).
const un = (r: any): any => r?.result ?? r;

function fmtUptime(sec: number): string {
  const h = Math.floor(sec / 3600);
  const m = Math.floor((sec % 3600) / 60);
  const s = sec % 60;
  const p = (n: number) => String(n).padStart(2, "0");
  return p(h) + ":" + p(m) + ":" + p(s);
}

// Raw backend states -> human words. The panel must never print FAILED /
// urlopen shapes (owner report 04.10): honest, but calm.
const FRIENDLY: Record<string, string> = {
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
function shortLabel(label: string): string {
  const m = /\[([A-Za-z0-9]{1,4})\]/.exec(label || "");
  return m ? m[1] : String(label || "").slice(0, 14);
}

// Classify backend errors into short human text (never dump urlopen guts).
function shortErr(e: any): string {
  const s = String(e || "").replace(/\s+/g, " ");
  if (/429|too many|rate.?limit/i.test(s)) return "provider rate-limited";
  if (/certificate|CERTIFICATE|ssl|verify failed/i.test(s)) return "TLS verify failed";
  if (/name resolution|Errno -[235]|getaddrinfo|nodename|Name or service/i.test(s)) return "no network (DNS)";
  if (/timed? ?out/i.test(s)) return "timeout";
  if (/urlopen|unreachable|http/i.test(s)) return "network error";
  return s.slice(0, 48) || "failed";
}

type Pending = { kind: "srv" | "on" | "off"; label: string; target: number; ts: number };

function Content() {
  const [on, setOn] = useState<boolean>(false);
  const [mode, setMode] = useState<Mode>("smart");
  const [meta, setMeta] = useState<string>("…");
  const [, setTick] = useState<number>(0);
  const sinceRef = useRef<number>(0);
  const [servers, setServers] = useState<DropdownOption[]>([]);
  const [srvIdx, setSrvIdx] = useState<number>(0);
  // Overlapping polls: a slow status probe (up to 30 s) must not stack ticks.
  const busyRef = useRef<boolean>(false);
  // Mode pick: shown immediately and kept for 8 s, like the power switch — without
  // it the dropdown snapped back for one poll and then flipped (the panel looked
  // broken while the backend was simply still switching).
  const modeWantRef = useRef<{ v: Mode; ts: number } | null>(null);
  const [quota, setQuota] = useState<string>("");
  const [rulesName, setRulesName] = useState<string>("");
  const [notice, setNotice] = useState<string>("");
  const noticeTsRef = useRef<number>(0);
  // Remount starts false: first paint must say Syncing, never stale OFF.
  const [synced, setSynced] = useState<boolean>(false);
  // Last rendered switch position (echo guard) + last commanded intent.
  // Steam re-fires onChange when a poll flips `checked` mid-transition
  // (off at 1s -> poll still CONNECTED -> checked true -> phantom vpn_up).
  const seenRef = useRef<boolean>(false);
  const wantRef = useRef<{ v: boolean; ts: number } | null>(null);
  // Server dropdown guards (live host showed real ping-pong here: 4/5/5/4/4/5
  // set_server calls per action). seenSrv = last rendered value; progSrvTs =
  // when WE last moved the dropdown (so a same-value re-fire can be told
  // apart from a deliberate re-tap).
  const seenSrvRef = useRef<number>(-1);
  const progSrvTsRef = useRef<number>(0);
  // Pending command: shown immediately as "switching to X…"/"connecting…"
  // until backend truth confirms it (or 15 s). Kills the dead 5-s-poll feel.
  const pendRef = useRef<Pending | null>(null);
  // Last observed actual_state (re-tap decisions).
  const stRef = useRef<string>("");

  function showNotice(s: string) {
    setNotice(s);
    noticeTsRef.current = Date.now();
  }

  function clearPending() {
    pendRef.current = null;
    setTick((t: number) => t + 1);
  }

  async function refresh() {
    if (busyRef.current) return;      // a slow probe must not stack polls
    busyRef.current = true;
    try {
      // One round trip, not three: panel syncs in ~1 poll, not ~3.
      const [sres, svres, qres]: any[] = await Promise.all([
        call("get_status"),
        call("get_servers"),
        call("get_quota"),
      ]);
      const st: any = un(sres);
      const ok: boolean = !!st?.ok;
      const actual: string = st?.actual_state || "?";
      const dm: string = st?.desired_mode || "smart";
      stRef.current = actual;
      // Switch follows INTENT (desired_mode), never a transient actual state:
      // mid-transition states must not flip the switch — a prop flip re-fires
      // Steam's onChange and that phantom call restarts or kills the service.
      const nowOn: boolean = ok ? dm !== "off" : seenRef.current;
      // Quiet window: while our own power command is in flight, keep showing
      // the commanded position instead of flapping with half-done truth.
      const quiet: boolean =
        wantRef.current !== null && Date.now() - wantRef.current.ts < 8000;
      if (!quiet) {
        setOn(nowOn);
        seenRef.current = nowOn;
      }
      // Honest clock: backend systemd timestamp wins (survives panel reopen);
      // local arming is the fallback. Cleared on drop; never armed mid-fail.
      if (nowOn && actual !== "FAILED" && actual !== "LOCKED") {
        const cs: number = Number(st?.connected_since || 0);
        sinceRef.current = cs > 0 ? cs * 1000 : (sinceRef.current || Date.now());
      } else {
        sinceRef.current = 0;
      }
      // Mode follows the backend, but our own pick wins while it is in flight
      // (same quiet-window idea as the power switch).
      const mq = modeWantRef.current;
      if (!(mq && Date.now() - mq.ts < 8000)) {
        setMode(dm === "full" ? "full" : dm === "proxy" ? "proxy" : "smart");
      }
      const ip: string = st?.exit_ip || "";
      // A failed status must not masquerade as a real link state.
      const fr: string = ok
        ? (FRIENDLY[actual] || String(actual).toLowerCase())
        : ("status: " + shortErr(st?.error || "unreadable"));
      const stag: string = shortLabel(String(st?.server_tag || ""));
      setMeta((stag ? stag + " · " : "") + fr + (ip ? " · " + ip : ""));
      setRulesName(st?.profile_name || st?.profile || "");
      const sv: any = un(svres);
      const list: any[] = sv?.servers || [];
      const active: string = sv?.active || "";
      setServers(
        list.map((s: any, i: number) => ({ data: i, label: s.remarks || ("Server " + (i + 1)) }))
      );
      const ai: number = list.findIndex((s: any) => s.address && s.address === active);
      const p = pendRef.current;
      if (p) {
        // Settle conditions: server pick -> selection persisted AND a settled
        // state (never claim "connected" within the first 3 s — that is the
        // old link still answering; the restart + transition marker follow).
        const settled =
          p.kind === "srv"
            ? ai === p.target && (
                actual === "DEGRADED" || actual === "FAILED" || actual === "LOCKED" ||
                actual === "OFF" || (actual === "CONNECTED" && Date.now() - p.ts > 3000)
              )
            : p.kind === "on"
              ? actual === "CONNECTED" || actual === "DEGRADED" || actual === "FAILED" || actual === "LOCKED"
              : actual === "OFF";
        if (settled || Date.now() - p.ts > 15000) {
          call("ui_log", "settle k=" + p.kind + " ai=" + ai + " act=" + actual + " dt=" + (Date.now() - p.ts)).catch(() => {});
          clearPending();
        }
      }
      // While our set_server is in flight, keep the user's pick rendered:
      // a stale selected-server.json must not flip the dropdown back.
      const srvBusy = pendRef.current?.kind === "srv";
      if (ai >= 0 && !srvBusy) {
        if (ai !== seenSrvRef.current) {
          call("ui_log", "srvset ai=" + ai + " prev=" + seenSrvRef.current).catch(() => {});
          progSrvTsRef.current = Date.now();
        }
        setSrvIdx(ai);
        seenSrvRef.current = ai;
      }
      const qq: any = un(qres)?.quota;
      if (qq && qq.used) {
        let upd = "";
        if (qq.ts) {
          const d = new Date(Number(qq.ts) * 1000);
          const p2 = (n: number) => String(n).padStart(2, "0");
          upd = " · " + p2(d.getHours()) + ":" + p2(d.getMinutes());
        }
        setQuota(String(qq.used) + upd);
      } else {
        setQuota("");
      }
    } catch (e) {
      setMeta("backend offline");
    } finally {
      busyRef.current = false;
    }
    // First paint must never claim OFF: remount starts false, truth arrives late.
    setSynced(true);
  }

  useEffect(() => {
    refresh();
    const t = setInterval(refresh, 5000);
    const u = setInterval(() => setTick((t: number) => t + 1), 1000);
    return () => {
      clearInterval(t);
      clearInterval(u);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function power(next: boolean) {
    wantRef.current = { v: next, ts: Date.now() };
    pendRef.current = { kind: next ? "on" : "off", label: "", target: 0, ts: Date.now() };
    const r: any = un(await call(next ? "vpn_up" : "vpn_down"));
    if (!r?.ok) {
      clearPending();
      showNotice((next ? "power on" : "power off") + " failed: " + shortErr(r?.out || r?.error));
    }
    setTick((t: number) => t + 1);
    setTimeout(refresh, 1200);
  }

  function onToggle(v: boolean) {
    // No-op echoes (Steam re-firing on a prop flip) must never reach backend.
    if (v === seenRef.current) return;
    seenRef.current = v;
    power(v);
  }

  async function switchMode(m: Mode) {
    modeWantRef.current = { v: m, ts: Date.now() };
    setMode(m);                        // instant feedback, no snap-back
    const r: any = un(await call("set_mode", m));
    if (!r?.ok) showNotice("mode: " + shortErr(r?.error || r?.out));
    setTimeout(refresh, 1200);
  }

  async function switchServer(i: number) {
    // a malformed dropdown event must never silently pick the first server
    if (!Number.isInteger(i) || i < 0 || i >= servers.length) return;
    if (i === seenSrvRef.current) {
      // Same value re-fire: either a Steam echo right after our own prop
      // change, or a deliberate re-tap of the same server.
      const isEcho = Date.now() - progSrvTsRef.current < 800;
      if (isEcho) { call("ui_log", "tap-echo i=" + i).catch(() => {}); return; }
      if (pendRef.current) { call("ui_log", "tap-busy i=" + i).catch(() => {}); return; }
      if (stRef.current === "CONNECTED") { call("ui_log", "tap-noop i=" + i).catch(() => {}); return; }
      // Deliberate re-tap on a non-connected link: retry (fresh set_server).
    }
    call("ui_log", "tap i=" + i + " prev=" + seenSrvRef.current + " st=" + stRef.current).catch(() => {});
    seenSrvRef.current = i;
    progSrvTsRef.current = Date.now();
    const label: string = shortLabel(String((servers[i] as any)?.label ?? ""));
    // Instant feedback only when there is a link to switch; with the VPN off
    // picking a server is a silent config change (the dropdown already moved).
    if (stRef.current !== "OFF") {
      pendRef.current = { kind: "srv", label: label, target: i, ts: Date.now() };
    }
    setSrvIdx(i);
    const r: any = un(await call("set_server", i));
    if (!r?.ok) {
      clearPending();
      showNotice("switch failed: " + shortErr(r?.error || r?.out));
    } else {
      call("ui_log", "set-ok i=" + i).catch(() => {});
    }
    setTick((t: number) => t + 1);
    setTimeout(refresh, 400);
    setTimeout(refresh, 1500);
  }

  const pend = pendRef.current;
  const noticeLive = notice !== "" && Date.now() - noticeTsRef.current < 12000;
  const bad = stRef.current === "DEGRADED" || stRef.current === "FAILED";
  let statusLine: string;
  if (!synced) {
    statusLine = "Syncing…";
  } else if (pend) {
    if (pend.kind === "srv") {
      statusLine = (on ? "● On" : "○ Off") + " (switching to " + pend.label + "…)";
    } else if (pend.kind === "on") {
      statusLine = "● On (connecting…)";
    } else {
      statusLine = "○ Off (turning off…)";
    }
  } else {
    statusLine = (on ? "● On" : "○ Off") + " (" + meta + ")";
  }

  return (
    <PanelSection title="Neodon VPN">
      <div>{"Status: " + statusLine}</div>
      <ToggleField
        label={on && sinceRef.current
          ? "VPN · " + fmtUptime(Math.floor((Date.now() - sinceRef.current) / 1000))
          : "VPN"}
        checked={on}
        onChange={(v: boolean) => onToggle(v)}
      />
      <Dropdown
        rgOptions={[
          { data: "smart", label: "PROXY" },
          { data: "full", label: "TUNNEL" },
          // shown only when the backend really is in socks-only mode, so the panel
          // never displays a mode it does not have (and never silently switches it)
          ...(mode === "proxy" ? [{ data: "proxy", label: "PROXY (no TUN)" }] : []),
        ]}
        selectedOption={mode}
        onChange={(v: any) => switchMode((v?.data as Mode) || "smart")}
        strDefaultLabel="Mode"
      />
      <Dropdown
        key={"srv-" + srvIdx}
        rgOptions={servers}
        selectedOption={srvIdx}
        onChange={(v: any) => switchServer(Number(v?.data ?? 0))}
        strDefaultLabel="Server"
      />
      {!pend && bad && (
        <div>↳ no link — pick another server, or tap this one again to retry</div>
      )}
      <ButtonItem layout="below" onClick={async () => {
        showNotice("refreshing subscription…");
        try {
          const r: any = un(await call("refresh_sub"));
          showNotice(r?.ok ? "subscription updated" : "refresh: " + shortErr(r?.error));
        } catch (e) {
          showNotice("refresh failed");
        }
        setTimeout(refresh, 2500);
      }}>
        Refresh (servers + usage)
      </ButtonItem>
      {noticeLive && <div>{notice}</div>}
      {quota !== "" && <div>Usage: {quota}</div>}
      {rulesName !== "" && <div>Traffic rules: {rulesName}</div>}
      <div>* rules come from the desktop app</div>
    </PanelSection>
  );
}

export default definePlugin(() => {
  return {
    title: <div className={staticClasses.Title}>Neodon VPN</div>,
    content: <Content />,
    icon: <FaShieldAlt />,
  };
});
