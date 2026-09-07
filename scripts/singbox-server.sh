#!/usr/bin/env bash
# sing-box VPN server picker (Bazzite)
DIR="$HOME/AI"
RAW="$DIR/neodon-sub/raw.json"
CFG="$DIR/singbox/config.json"
CFG_FULL="$DIR/singbox/config-full.json"
CFG_PROXY="$DIR/singbox/config-proxy.json"
SB="/usr/local/bin/sing-box"
export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"

build_outbound() {
  python3 - "$RAW" "$1" <<'PY'
import json, sys
data = json.load(open(sys.argv[1]))
try:
    cfg = data[int(sys.argv[2])]
except (IndexError, ValueError):
    sys.exit(1)
for o in cfg.get("outbounds") or []:
    if o.get("protocol") != "vless":
        continue
    s = ((o.get("settings") or {}).get("vnext") or [{}])[0]
    user = (s.get("users") or [{}])[0]
    st = o.get("streamSettings") or {}
    out = {
        "type": "vless",
        "tag": "proxy",
        "server": s.get("address"),
        "server_port": s.get("port"),
        "uuid": user.get("id"),
    }
    flow = user.get("flow") or ""
    if flow:
        out["flow"] = flow
    net = st.get("network")
    if net == "ws":
        ws = st.get("wsSettings") or {}
        t = {"type": "ws", "path": ws.get("path") or "/"}
        host = ws.get("host") or (ws.get("headers") or {}).get("Host")
        if host:
            t["headers"] = {"Host": host}
        out["transport"] = t
    elif net == "grpc":
        gr = st.get("grpcSettings") or {}
        out["transport"] = {"type": "grpc", "service_name": gr.get("serviceName") or "xyz"}
    if st.get("security") == "reality":
        r = st.get("realitySettings") or {}
        out["tls"] = {
            "enabled": True,
            "server_name": r.get("serverName"),
            "utls": {"enabled": True, "fingerprint": r.get("fingerprint") or "chrome"},
            "reality": {
                "enabled": True,
                "public_key": r.get("publicKey"),
                "short_id": r.get("shortId") or "",
            },
        }
    # normalize bogus qq fingerprint -> chrome
    if "tls" in out and "utls" in out["tls"]:
        if out["tls"]["utls"].get("fingerprint") in ("qq","QQ"):
            out["tls"]["utls"]["fingerprint"] = "chrome"
    print(json.dumps(out))
    sys.exit(0)
sys.exit(1)
PY
}

list_servers() {
  python3 - "$RAW" <<'PY'
import json, sys
data = json.load(open(sys.argv[1]))
for i, cfg in enumerate(data):
    for o in cfg.get("outbounds") or []:
        if o.get("protocol") != "vless":
            continue
        s = ((o.get("settings") or {}).get("vnext") or [{}])[0]
        st = o.get("streamSettings") or {}
        print(f"{i}) [{s.get('address')}] {s.get('address')}:{s.get('port')} ({st.get('network')}/{st.get('security') or 'none'})")
        break
PY
}

set_server() {
  local n="$1" out name
  if ! [[ "$n" =~ ^[0-9]+$ ]]; then
    echo "ОШИБКА: '$n' — не номер"
    return 1
  fi
  out=$(build_outbound "$n") || { echo "ОШИБКА: сервер $n не найден"; return 1; }
  name=$(echo "$out" | python3 -c 'import json,sys; print(json.load(sys.stdin)["server"])')
  cp "$CFG" "$CFG.bak" && cp "$CFG_FULL" "$CFG_FULL.bak" && cp "$CFG_PROXY" "$CFG_PROXY.bak"
  python3 - "$CFG" "$CFG_FULL" "$CFG_PROXY" "$out" <<'PY'
import json, sys
cfg, cfg_full, cfg_proxy, out = sys.argv[1], sys.argv[2], sys.argv[3], json.loads(sys.argv[4])
for p in (cfg, cfg_full, cfg_proxy):
    d = json.load(open(p))
    d["outbounds"] = [out if o.get("tag") == "proxy" else o for o in d["outbounds"]]
    with open(p, "w") as f:
        json.dump(d, f, indent=2, ensure_ascii=False)
        f.write("\n")
PY
  if "$SB" check -c "$CFG" >/dev/null 2>&1 && "$SB" check -c "$CFG_FULL" >/dev/null 2>&1 && "$SB" check -c "$CFG_PROXY" >/dev/null 2>&1; then
    st=$(systemctl --user is-active sing-box.service 2>/dev/null)
    stf=$(systemctl --user is-active sing-box-full.service 2>/dev/null)
    if [ "$st" = active ] || [ "$st" = activating ]; then
      systemctl --user restart sing-box.service
      for i in $(seq 1 15); do systemctl --user is-active sing-box.service | grep -q active && break; sleep 1; done
    elif [ "$stf" = active ] || [ "$stf" = activating ]; then
      systemctl --user restart sing-box-full.service
      # киллсвитч allowlist завязан на IP старого сервера — переустанавливаем
      # (install идемпотентен: добавляет IP нового сервера, ничего не флашит)
      for i in $(seq 1 15); do systemctl --user is-active sing-box-full.service | grep -q active && break; sleep 1; done
      bash ~/AI/singbox/killswitch.sh install >/dev/null 2>&1 && echo "KILLSWITCH: allowlist обновлён под " || echo "WARN: killswitch reinstall failed"
    elif [ "$(systemctl --user is-active sing-box-proxy.service 2>/dev/null)" = active ] || [ "$(systemctl --user is-active sing-box-proxy.service 2>/dev/null)" = activating ]; then
      systemctl --user restart sing-box-proxy.service
      for i in $(seq 1 15); do systemctl --user is-active sing-box-proxy.service | grep -q active && break; sleep 1; done
    fi
      # sync GUI header tag
    TAG=$(python3 - "$RAW" "$n" 2>/dev/null <<'PYEOF2'
import json,sys
try: print(json.load(open(sys.argv[1]))[int(sys.argv[2])].get("remarks",""))
except: print("")
PYEOF2
)
    if [ -z "$TAG" ]; then TAG=$(echo "$out" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("server",""))'); fi
    python3 - "$out" "$TAG" <<'PYEOF3' 2>/dev/null || true
import json, time, sys, os
out=json.loads(sys.argv[1]); tag=sys.argv[2]
sel={"tag": tag or out.get("server",""), "server": out["server"], "server_port": out["server_port"], "updated": time.strftime("%Y-%m-%dT%H:%M:%S")}
open(os.path.expanduser("~/AI/singbox/selected-server.json"),"w").write(json.dumps(sel, ensure_ascii=False, indent=2))
PYEOF3
    _last="/tmp/neodon-last-notify"; _now=$(date +%s); _prev=$(cat "$_last" 2>/dev/null || echo 0); if [ $((_now - _prev)) -ge 10 ]; then notify-send "VPN" "Сервер: $name" 2>/dev/null || true; echo "$_now" > "$_last"; fi
    echo "OK: переключено на сервер $name"
  else
    cp "$CFG.bak" "$CFG"
    cp "$CFG_FULL.bak" "$CFG_FULL"
    cp "$CFG_PROXY.bak" "$CFG_PROXY"
    echo "ОШИБКА: конфигурация не прошла sing-box check — восстановлено"
    return 1
  fi
}

case "${1:-}" in
  "")
    list_servers
    echo
    read -r -p "Выбери номер: " n
    set_server "$n"
    echo
    read -r -p "Нажми Enter..."
    ;;
  list) list_servers ;;
  set) set_server "${2:-}" ;;
  *)
    echo "Использование: $0 [list|set <N>]" >&2
    exit 1
    ;;
esac
