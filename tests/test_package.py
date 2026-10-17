"""The package imports without the optional ml dependencies."""

import subprocess
import sys

import stand
from stand.config import CONFIGS, get_config


def test_package_imports() -> None:
    assert stand.__doc__


def test_config_lookup() -> None:
    assert get_config("retail").domain == "retail"
    assert set(CONFIGS) >= {"retail", "airline", "telecom"}


def test_import_does_not_load_ml_deps() -> None:
    code = "import sys, stand.target; assert not {'torch', 'sklearn'} & set(sys.modules)"
    subprocess.run([sys.executable, "-c", code], check=True)
