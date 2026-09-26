from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest


CONFIGS = ["config.json", "config-full.json", "config-proxy.json"]


@pytest.mark.l2
def test_profiles_smoke(singbox_root: Path):
    profiles = singbox_root / "profiles"
    if not profiles.is_dir():
        pytest.skip("profiles/ not mounted")
    files = sorted(profiles.glob("*.json"))
    REQUIRED = {"default", "basic-set", "ru-bez-vpn", "popular-ai",
                "social-networks", "only-unavailable", "socseti-vpn"}
    names = {f.stem for f in files}
    missing = REQUIRED - names
    assert not missing, f"missing required profiles: {sorted(missing)}"
    assert len(files) >= 7, f"expected >=7 profiles, found {len(files)}"
    bad = []
    for p in files:
        try:
            obj = json.loads(p.read_text(encoding="utf-8"))
        except Exception as exc:
            bad.append(f"{p.name}: invalid JSON: {exc}")
            continue
        if not isinstance(obj, dict):
            bad.append(f"{p.name}: root is not object")
            continue
        if "route" in obj and "rules" in obj["route"] and not isinstance(obj["route"]["rules"], list):
            bad.append(f"{p.name}: route.rules is not list")
    assert not bad, "\\n".join(bad)


@pytest.mark.l2
@pytest.mark.parametrize("name", CONFIGS)
def test_singbox_config_validity(singbox_root: Path, name: str):
    cfg = singbox_root / name
    if not cfg.exists():
        pytest.skip(f"{cfg} not found")
    binary = Path("/usr/local/bin/sing-box")
    if not binary.exists():
        pytest.skip("/usr/local/bin/sing-box not installed")
    cp = subprocess.run([str(binary), "check", "-c", str(cfg)], text=True, capture_output=True)
    assert cp.returncode == 0, cp.stderr or cp.stdout


@pytest.mark.l2
def test_selected_server_json_shape(singbox_root: Path):
    p = singbox_root / "selected-server.json"
    if not p.exists():
        pytest.skip("selected-server.json not mounted")
    obj = json.loads(p.read_text(encoding="utf-8"))
    assert isinstance(obj, dict)
    for key in ("tag", "server", "server_port", "updated"):
        assert key in obj
    assert isinstance(obj["tag"], str)
    assert isinstance(obj["server"], str)
    assert isinstance(obj["server_port"], int)
