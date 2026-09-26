from __future__ import annotations

import os
from pathlib import Path

import pytest


DEFAULT_REPO = Path(os.path.expanduser("~/AI/neodon-vpn"))
DEFAULT_BACKEND = Path(os.path.expanduser("~/AI/singbox"))


def repo_root() -> Path:
    return Path(os.environ.get("NEODON_REPO", DEFAULT_REPO))


def backend_root() -> Path:
    return Path(os.environ.get("NEODON_BACKEND", DEFAULT_BACKEND))


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "l1: fast/offscreen/contract checks")
    config.addinivalue_line("markers", "l2: component checks")


@pytest.fixture(scope="session")
def neodon_repo() -> Path:
    return repo_root()


@pytest.fixture(scope="session")
def singbox_root() -> Path:
    return backend_root()


def live_enabled() -> bool:
    return os.environ.get("NEODON_LIVE", "0") == "1"


@pytest.fixture(scope="session")
def require_live():
    if not live_enabled():
        pytest.skip("NEODON_LIVE=1 is required")
