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

type Mode = "smart" | "full";

// Loader answers {result: ...} over WS; unwrap defensively (ponytail:
// one line, covers both wrapped and raw shapes).
const un = (r: any): any => r?.result ?? r;

function fmtUptime(sec: number): string {
  const h = Math.floor(sec / 3600);
  const m = Math.floor((sec % 3600) / 60);
  const s = sec % 60;
  const p = (n: number) => String(n).padStart(2, "0");
  return h + ":" + p(m) + ":" + p(s);
}

function Content() {
  const [on, setOn] = useState<boolean>(false);
  const [mode, setMode] = useState<Mode>("smart");
  const [meta, setMeta] = useState<string>("…");
  const [, setTick] = useState<number>(0);
  const sinceRef = useRef<number>(0);
  const [servers, setServers] = useState<DropdownOption[]>([]);
  const [srvIdx, setSrvIdx] = useState<number>(0);
  const [quota, setQuota] = useState<string>("");
  const [rulesName, setRulesName] = useState<string>("");

  async function refresh() {
    try {
      const st: any = un(await call("get_status"));
      const ok: boolean = !!st?.ok;
      const actual: string = st?.actual_state || "?";
      const nowOn: boolean = ok && actual === "CONNECTED";
      // Honest clock: backend systemd timestamp wins (survives panel
      // reopen); local arming is the fallback. Cleared on drop.
      if (nowOn) {
        const cs: number = Number(st?.connected_since || 0);
        sinceRef.current = cs > 0 ? cs * 1000 : (sinceRef.current || Date.now());
      } else {
        sinceRef.current = 0;
      }
      setOn(nowOn);
      const dm: string = st?.desired_mode || "smart";
      setMode(dm === "full" ? "full" : "smart");
      const ip: string = st?.exit_ip || "—";
      setMeta(actual + " · " + ip);
      setRulesName(st?.profile_name || st?.profile || "");
      const sv: any = un(await call("get_servers"));
      const list: any[] = sv?.servers || [];
      const active: string = sv?.active || "";
      setServers(
        list.map((s: any, i: number) => ({ data: i, label: s.remarks || ("Server " + (i + 1)) }))
      );
      const ai: number = list.findIndex((s: any) => s.address && s.address === active);
      // Never snap back to first on a backend hiccup: keep current idx.
      if (ai >= 0) setSrvIdx(ai);
      const qq: any = un(await call("get_quota"))?.quota;
      setQuota(qq && qq.used ? String(qq.used) : "");
    } catch (e) {
      setMeta("poll error");
    }
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
    await call(next ? "vpn_up" : "vpn_down");
    setTimeout(refresh, 1200);
  }

  async function switchMode(m: Mode) {
    await call("set_mode", m);
    setTimeout(refresh, 1200);
  }

  async function switchServer(i: number) {
    if (servers.length === 0) return;
    setSrvIdx(i);
    await call("set_server", i);
    setTimeout(refresh, 1500);
  }

  return (
    <PanelSection title="Neodon VPN">
      <div>Status: {on ? "● On" : "○ Off"} ({meta})</div>
      <ToggleField
        label={on && sinceRef.current
          ? "VPN · " + fmtUptime(Math.floor((Date.now() - sinceRef.current) / 1000))
          : "VPN"}
        checked={on}
        onChange={(v: boolean) => power(v)}
      />
      <Dropdown
        rgOptions={[
          { data: "smart", label: "PROXY" },
          { data: "full", label: "TUNNEL" },
        ]}
        selectedOption={mode}
        onChange={(v: any) => switchMode((v?.data as Mode) || "smart")}
        strDefaultLabel="Mode"
      />
      <Dropdown
        rgOptions={servers}
        selectedOption={srvIdx}
        onChange={(v: any) => switchServer(Number(v?.data ?? 0))}
        strDefaultLabel="Server"
      />
      <ButtonItem layout="below" onClick={async () => {
        setMeta("refreshing subscription…");
        await call("refresh_sub");
        refresh();
      }}>
        Refresh (servers + usage)
      </ButtonItem>
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
