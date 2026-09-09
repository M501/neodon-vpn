import { useEffect, useState } from "react";
import {
  definePlugin,
  PanelSection,
  ToggleField,
  Dropdown,
  DropdownOption,
  ButtonItem,
  staticClasses,
} from "@decky/ui";
import { FaShieldAlt } from "react-icons/fa";

// ServerAPI type left as any: @decky/ui no longer re-exports it,
// and structural typing is all this panel needs.
type ServerAPI = any;

type Mode = "smart" | "full";

function Content({ serverAPI }: { serverAPI: ServerAPI }) {
  const [on, setOn] = useState<boolean>(false);
  const [mode, setMode] = useState<Mode>("smart");
  const [meta, setMeta] = useState<string>("…");
  const [servers, setServers] = useState<DropdownOption[]>([]);
  const [srvIdx, setSrvIdx] = useState<number>(0);
  const [quota, setQuota] = useState<string>("");

  async function refresh() {
    try {
      const st: any = await serverAPI.callPluginMethod("get_status", {});
      const ok: boolean = !!st?.result?.ok;
      const actual: string = st?.result?.actual_state || "?";
      setOn(ok && actual === "CONNECTED");
      const dm: string = st?.result?.desired_mode || "smart";
      setMode(dm === "full" ? "full" : "smart");
      const ip: string = st?.result?.exit_ip || "—";
      setMeta(actual + " · " + ip);
      const sv: any = await serverAPI.callPluginMethod("get_servers", {});
      const list: any[] = sv?.result?.servers || [];
      const active: string = sv?.result?.active || "";
      setServers(
        list.map((s: any, i: number) => ({ data: i, label: s.remarks || ("Сервер " + (i + 1)) }))
      );
      const ai: number = Math.max(0, list.findIndex((s: any) => s.address && s.address === active));
      setSrvIdx(ai);
      const q: any = await serverAPI.callPluginMethod("get_quota", {});
      const qq: any = q?.result?.quota;
      setQuota(qq && qq.used ? String(qq.used) : "");
    } catch (e) {
      setMeta("ошибка опроса");
    }
  }

  useEffect(() => {
    refresh();
    const t = setInterval(refresh, 5000);
    return () => clearInterval(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function power(next: boolean) {
    await serverAPI.callPluginMethod(next ? "vpn_up" : "vpn_down", {});
    setTimeout(refresh, 1200);
  }

  async function switchMode(m: Mode) {
    await serverAPI.callPluginMethod("set_mode", { mode: m });
    setTimeout(refresh, 1200);
  }

  async function switchServer(i: number) {
    await serverAPI.callPluginMethod("set_server", { idx: i });
    setTimeout(refresh, 1500);
  }

  return (
    <PanelSection title="Neodon VPN">
      <div>Статус: {on ? "● Вкл" : "○ Выкл"} ({meta})</div>
      <ToggleField
        label="VPN"
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
        strDefaultLabel="Режим"
      />
      <Dropdown
        rgOptions={servers}
        selectedOption={srvIdx}
        onChange={(v: any) => switchServer(Number(v?.data ?? 0))}
        strDefaultLabel="Сервер"
      />
      <ButtonItem layout="below" onClick={async () => {
        setMeta("обновление подписки…");
        await serverAPI.callPluginMethod("refresh_sub", {});
        refresh();
      }}>
        Обновить (серверы + трафик)
      </ButtonItem>
      {quota !== "" && <div>Трафик: {quota}</div>}
    </PanelSection>
  );
}

export default definePlugin((serverAPI: ServerAPI) => {
  return {
    title: <div className={staticClasses.Title}>Neodon VPN</div>,
    content: <Content serverAPI={serverAPI} />,
    icon: <FaShieldAlt />,
  };
});
