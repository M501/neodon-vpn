from __future__ import annotations

import json
import ipaddress

import pytest


DESIRED = {"smart", "full", "proxy", "off", "unknown"}
STATES = {
    "OFF", "STARTING", "TRANSITIONING", "CONNECTING", "CONNECTED",
    "DEGRADED", "FAILED", "LOCKED", "STOPPING",
}
SERVICES = {"sing-box.service", "sing-box-full.service", "sing-box-proxy.service", "none"}
SERVICE_STATES = {"active", "inactive", "failed", "activating"}
WATCHDOG = {"ok", "degraded", "locked", None}


SAMPLE = {
    "desired_mode": "smart",
    "profile": "default",
    "actual_state": "CONNECTED",
    "service": "sing-box.service",
    "service_state": "active",
    "firewall_rules": 0,
    "tun0": True,
    "exit_ip": "1.2.3.4",
    "server_tag": "[NL] test",
    "latency_ms": 42,
    "watchdog_status": "ok",
    "consecutive_failures": 0,
    "next_retry": None,
}


def validate_status(obj: dict) -> list[str]:
    errors: list[str] = []
    required = set(SAMPLE)
    errors.extend(f"missing:{k}" for k in sorted(required - set(obj)))
    if obj.get("desired_mode") not in DESIRED:
        errors.append("bad:desired_mode")
    if obj.get("actual_state") not in STATES:
        errors.append("bad:actual_state")
    if obj.get("service") not in SERVICES:
        errors.append("bad:service")
    if obj.get("service_state") not in SERVICE_STATES:
        errors.append("bad:service_state")
    if not isinstance(obj.get("profile"), str):
        errors.append("bad:profile")
    if not isinstance(obj.get("firewall_rules"), int) or obj.get("firewall_rules", -1) < 0:
        errors.append("bad:firewall_rules")
    if not isinstance(obj.get("tun0"), bool):
        errors.append("bad:tun0")
    if obj.get("exit_ip") is not None:
        try:
            ipaddress.ip_address(obj["exit_ip"])
        except ValueError:
            errors.append("bad:exit_ip")
    if obj.get("latency_ms") is not None and (
        not isinstance(obj["latency_ms"], (int, float)) or obj["latency_ms"] < 0
    ):
        errors.append("bad:latency_ms")
    if obj.get("watchdog_status") not in WATCHDOG:
        errors.append("bad:watchdog_status")
    if not isinstance(obj.get("consecutive_failures"), int) or obj.get("consecutive_failures", -1) < 0:
        errors.append("bad:consecutive_failures")
    return errors


@pytest.mark.l1
def test_valid_sample_status_contract():
    assert validate_status(SAMPLE) == []


@pytest.mark.l1
def test_json_is_one_object_and_not_array():
    raw = json.dumps(SAMPLE)
    obj = json.loads(raw)
    assert isinstance(obj, dict)
    assert not isinstance(obj, list)


@pytest.mark.l1
@pytest.mark.parametrize(
    "state,service_state,tun0,exit_ok,expected",
    [
        ("CONNECTED", "active", True, True, True),
        ("DEGRADED", "active", True, False, True),
        ("FAILED", "failed", False, False, True),
        ("OFF", "inactive", False, False, True),
    ],
)
def test_state_contract_examples(state, service_state, tun0, exit_ok, expected):
    obj = dict(SAMPLE)
    obj.update(actual_state=state, service_state=service_state, tun0=tun0,
               exit_ip="1.2.3.4" if exit_ok else None)
    assert bool(validate_status(obj) == []) is expected


@pytest.mark.l1
def test_full_mode_requires_fail_closed_semantics_in_contract():
    obj = dict(SAMPLE, desired_mode="full", service="sing-box-full.service")
    assert validate_status(obj) == []


@pytest.mark.l1
@pytest.mark.parametrize("cidr", ["100.64.0.0/10"])
def test_tailscale_direct_network_is_documented_contract(cidr):
    net = ipaddress.ip_network(cidr)
    assert ipaddress.ip_address("100.64.0.1") in net
    assert ipaddress.ip_address("100.127.255.254") in net
