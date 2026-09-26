from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest


BACKEND_SCRIPTS = [
    "singbox-toggle.sh",
    "singbox-server.sh",
    "killswitch.sh",
    "dns-fix.sh",
    "apply-profile.py",
    "neodon-hostctl",
]


@pytest.mark.l1
def test_expected_backend_entrypoints_exist(singbox_root: Path):
    missing = [name for name in BACKEND_SCRIPTS if not (singbox_root / name).exists()]
    if missing:
        pytest.skip(f"backend not mounted at {singbox_root}; missing: {', '.join(missing)}")


@pytest.mark.l1
def test_gui_entrypoint_exists(neodon_repo: Path):
    p = neodon_repo / "neodon-vpn.py"
    if not p.exists():
        pytest.skip(f"GUI source not mounted at {p}")


@pytest.mark.l1
def test_shell_syntax_for_known_scripts(singbox_root: Path):
    sh_files = list(singbox_root.glob("*.sh"))
    if not sh_files:
        pytest.skip(f"no shell scripts found in {singbox_root}")
    failures = []
    for path in sh_files:
        cp = subprocess.run(["bash", "-n", str(path)], text=True, capture_output=True)
        if cp.returncode:
            failures.append(f"{path.name}: {cp.stderr.strip()}")
    assert not failures, "\\n".join(failures)


@pytest.mark.l1
def test_python_compile_gate(neodon_repo: Path, singbox_root: Path):
    candidates = [neodon_repo / "neodon-vpn.py", singbox_root / "apply-profile.py"]
    present = [p for p in candidates if p.exists()]
    if not present:
        pytest.skip("known Python sources not mounted")
    failures = []
    for path in present:
        cp = subprocess.run([sys.executable, "-m", "py_compile", str(path)], text=True, capture_output=True)
        if cp.returncode:
            failures.append(f"{path.name}: {cp.stderr.strip()}")
    assert not failures, "\\n".join(failures)
