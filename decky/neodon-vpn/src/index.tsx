import { useEffect, useState } from "react";
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

function Content() {
  const [on, setOn] = useState<boolean>(false);
  const [mode, setMode] = useState<Mode>("smart");
  const [meta, setMeta] = useState<string>("…");
  const [servers, setServers] = useState<DropdownOption[]>([]);
  const [srvIdx, setSrvIdx] = useState<number>(0);
  const [quota, setQuota] = useState<string>("");
  const [profile, setProfile] = useState<string>("");

  async function refresh() {
    try {
      const st: any = un(await call("get_status"));
      const ok: boolean = !!st?.ok;
      const actual: string = st?.actual_state || "?";
      setOn(ok && actual === "CONNECTED");
      const dm: string = st?.desired_mode || "smart";
      setMode(dm === "full" ? "full" : "smart");
      const ip: string = st?.exit_ip || "—";
      setMeta(actual + " · " + ip);
      setProfile(st?.profile || "");
      const sv: any = un(await call("get_servers"));
      const list: any[] = sv?.servers || [];
      const active: string = sv?.active || "";
      setServers(
        list.map((s: any, i: number) => ({ data: i, label: s.remarks || ("Сервер " + (i + 1)) }))
      );
      const ai: number = Math.max(0, list.findIndex((s: any) => s.address && s.address === active));
      setSrvIdx(ai);
      const qq: any = un(await call("get_quota"))?.quota;
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
    await call(next ? "vpn_up" : "vpn_down");
    setTimeout(refresh, 1200);
  }

  async function switchMode(m: Mode) {
    await call("set_mode", m);
    setTimeout(refresh, 1200);
  }

  async function stepServer(d: number) {
    if (servers.length === 0) return;
    const next: number = (srvIdx + d + servers.length) % servers.length;
    setSrvIdx(next);
    await call("set_server", next);
    setTimeout(refresh, 1500);
  }

  const curLabel: string =
    servers.length > 0 ? String(servers[srvIdx]?.label || ("Сервер " + (srvIdx + 1))) : "…";

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
      <div>{curLabel} ({servers.length > 0 ? srvIdx + 1 : 0}/{servers.length})</div>
      <ButtonItem layout="below" onClick={() => stepServer(-1)}>
        ◀ Предыдущий сервер
      </ButtonItem>
      <ButtonItem layout="below" onClick={() => stepServer(1)}>
        Следующий сервер ▶
      </ButtonItem>
      <ButtonItem layout="below" onClick={async () => {
        setMeta("обновление подписки…");
        await call("refresh_sub");
        refresh();
      }}>
        Обновить (серверы + трафик)
      </ButtonItem>
      {quota !== "" && <div>Трафик: {quota}</div>}
      {profile !== "" && <div>Профиль: {profile} (как в десктопе)</div>}
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
