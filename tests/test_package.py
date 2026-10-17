"""The package imports without the optional ml dependencies and without tau2 data."""

import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

import stand
from stand.config import CONFIGS, get_config

ROOT = Path(__file__).resolve().parents[1]


def test_package_imports() -> None:
    assert stand.__doc__


def test_config_lookup() -> None:
    assert get_config("retail").domain == "retail"
    assert set(CONFIGS) >= {"retail", "airline", "telecom"}


def test_import_does_not_load_ml_deps() -> None:
    code = "import sys, stand.target; assert not {'torch', 'sklearn'} & set(sys.modules)"
    subprocess.run([sys.executable, "-c", code], check=True)


def test_tau2_code_and_data_pinned_to_same_commit() -> None:
    """uv.lock (code) and the submodule pointer (data) must name one tau2 commit."""
    lock = (ROOT / "uv.lock").read_text()
    code_commit = re.search(r"tau2-bench\?rev=\w+#(\w+)", lock)
    assert code_commit, "tau2 git source not found in uv.lock"

    if shutil.which("git") is None or not (ROOT / ".git").exists():
        pytest.skip("not a git checkout")
    tree = subprocess.run(
        ["git", "ls-tree", "HEAD", "third_party/tau2-bench"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split()
    if not tree:
        pytest.skip("submodule pointer not committed yet")
    assert tree[2] == code_commit.group(1)
