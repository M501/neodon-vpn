from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

import pytest


SECRET_PATTERNS = [
    re.compile(r"(?:sk-|ghp_|github_pat_|xox[baprs]-)[A-Za-z0-9_\-]{12,}"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
]
TEXT_EXTS = {".sh", ".py", ".json", ".md", ".txt", ".service", ".desktop", ".conf"}


@pytest.mark.l2
def test_install_dry_run(neodon_repo: Path, tmp_path: Path):
    installer = neodon_repo / "install.sh"
    if not installer.exists():
        pytest.skip("install.sh not mounted")
    before = sorted(str(p.relative_to(neodon_repo)) for p in neodon_repo.rglob("*") if p.is_file())
    env = os.environ.copy()
    env["HOME"] = str(tmp_path)
    cp = subprocess.run(["bash", str(installer), "--dry-run"], cwd=neodon_repo,
                        env=env, text=True, capture_output=True, timeout=60)
    assert cp.returncode == 0, cp.stderr or cp.stdout
    after = sorted(str(p.relative_to(neodon_repo)) for p in neodon_repo.rglob("*") if p.is_file())
    assert before == after, "--dry-run mutated repository contents"


@pytest.mark.l1
def test_static_secret_scan(neodon_repo: Path):
    if not neodon_repo.exists():
        pytest.skip("repo not mounted")
    findings = []
    for p in neodon_repo.rglob("*"):
        if not p.is_file() or p.suffix.lower() not in TEXT_EXTS:
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for rx in SECRET_PATTERNS:
            if rx.search(text):
                findings.append(str(p.relative_to(neodon_repo)))
                break
    assert not findings, "possible secret material found in: " + ", ".join(sorted(set(findings)))
