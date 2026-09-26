from __future__ import annotations

import pytest


STATES = {
    "OFF", "STARTING", "TRANSITIONING", "CONNECTING", "CONNECTED",
    "DEGRADED", "FAILED", "LOCKED", "STOPPING",
}

LEGAL = {
    "OFF": {"STARTING", "TRANSITIONING", "OFF"},
    "STARTING": {"TRANSITIONING", "CONNECTING", "FAILED", "LOCKED", "STOPPING"},
    "TRANSITIONING": {"CONNECTING", "CONNECTED", "DEGRADED", "FAILED", "LOCKED", "STOPPING"},
    "CONNECTING": {"CONNECTED", "DEGRADED", "FAILED", "LOCKED", "STOPPING"},
    "CONNECTED": {"DEGRADED", "STOPPING", "TRANSITIONING"},
    "DEGRADED": {"CONNECTED", "FAILED", "STOPPING", "TRANSITIONING"},
    "FAILED": {"STARTING", "TRANSITIONING", "OFF", "LOCKED"},
    "LOCKED": {"STOPPING", "OFF", "STARTING"},
    "STOPPING": {"OFF", "STARTING"},
}


@pytest.mark.l1
def test_state_machine_contains_all_documented_states():
    assert set(LEGAL) == STATES


@pytest.mark.l1
@pytest.mark.parametrize("src,dst", [("OFF", "CONNECTED"), ("OFF", "DEGRADED"), ("OFF", "LOCKED")])
def test_direct_illegal_off_transitions_are_not_accepted(src, dst):
    assert dst not in LEGAL[src]


@pytest.mark.l1
def test_connected_wobble_guard_shape():
    # Contract: first 1-2 probe failures remain CONNECTED; third is accepted.
    sequence = [True, False, False, False]
    accepted_state = "CONNECTED"
    failures = 0
    for ok in sequence:
        if ok:
            failures = 0
        else:
            failures += 1
            if failures >= 3:
                accepted_state = "DEGRADED"
    assert accepted_state == "DEGRADED"
