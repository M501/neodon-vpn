#!/usr/bin/env bash
# sing-box VPN server picker — INSTANT selector switch via Clash API (spec 036).
# No config patching / no service restart: the live configs carry all nodes,
# urltest "auto" and selector "proxy" (Clash API on 127.0.0.1:9090).
# Contract kept: `list` | `set <N>` (prints "OK: ..." on success).
DIR="$HOME/AI"
RAW="$DIR/neodon-sub/raw.json"
SEL="$DIR/singbox/selected-server.json"
PREF="$DIR/singbox/.preferred-server"
API="http://127.0.0.1:9090"
export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"

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

_srv_meta() {  # $1=idx -> "<address> <remarks-one-word>"
  python3 - "$RAW" "$1" <<'PY'
import json, sys
try:
    cfg = json.load(open(sys.argv[1]))[int(sys.argv[2])]
except Exception:
    sys.exit(1)
for o in cfg.get("outbounds") or []:
    if o.get("protocol") != "vless":
        continue
    s = ((o.get("settings") or {}).get("vnext") or [{}])[0]
    print(s.get("address"), (cfg.get("remarks") or "").replace(" ", "_"))
    sys.exit(0)
sys.exit(1)
PY
}

_write_selected() {  # $1=idx $2=address $3=tag
  python3 - "$RAW" "$SEL" "$1" "$2" "$3" <<'PY'
import json, sys, time
raw, sel, idx, addr, tag = sys.argv[1:6]
port = 443
try:
    cfg = json.load(open(raw))[int(idx)]
    for o in cfg.get("outbounds") or []:
        if o.get("protocol") == "vless":
            port = (((o.get("settings") or {}).get("vnext") or [{}])[0]).get("port") or 443
            break
except Exception:
    pass
open(sel, "w").write(json.dumps({
    "tag": tag.replace("_", " "), "server": addr, "server_port": port,
    "updated": time.strftime("%Y-%m-%dT%H:%M:%S")}, ensure_ascii=False, indent=2))
PY
}

_put_selector() {  # $1=idx -> rc0 when the selector switched to n<idx>
  local i
  for i in 1 2 3 4 5; do
    curl -s -m 3 -X PUT -H 'Content-Type: application/json' \
      -d "{\"name\":\"n$1\"}" "$API/proxies/proxy" >/dev/null 2>&1 && return 0
    sleep 0.3
  done
  return 1
}

set_server() {
  local n="$1" meta addr tag u
  if ! [[ "$n" =~ ^[0-9]+$ ]]; then
    echo "ОШИБКА: '$n' — не номер"
    return 1
  fi
  meta=$(_srv_meta "$n") || { echo "ОШИБКА: сервер $n не найден"; return 1; }
  addr=${meta%% *}; tag=${meta#* }

  # persist intent first (panel/status read selected-server.json; startup applies it)
  _write_selected "$n" "$addr" "$tag"
  echo "$n" > "$PREF"

  if _put_selector "$n"; then
    echo "OK: переключено на сервер $addr"
    return 0
  fi

  # API down while a service is active: restart the ACTIVE unit only (rare fallback)
  for u in sing-box.service sing-box-full.service sing-box-proxy.service; do
    if systemctl --user is-active "$u" >/dev/null 2>&1; then
      touch "$HOME/AI/singbox/.transitioning"
      systemctl --user restart "$u"
      if _put_selector "$n"; then
        echo "OK: переключено на сервер $addr (после рестарта)"
        return 0
      fi
      echo "ОШИБКА: не удалось применить переключение"
      return 1
    fi
  done

  echo "OK: выбор сохранён (применится при включении)"
  return 0
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
