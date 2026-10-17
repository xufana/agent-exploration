"""Testbed: τ-bench agents as black boxes.

Runs before any tau2 import: tau2 reads env vars and logs at DEBUG on import,
and resolves its data directory once, from TAU2_DATA_DIR.
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from loguru import logger

load_dotenv()

logger.remove()
logger.add(sys.stderr, level=os.getenv("STAND_LOG_LEVEL", "WARNING"))

# tau2 is installed from git without its data/; take it from the submodule.
_SUBMODULE_DATA = Path(__file__).resolve().parents[2] / "third_party" / "tau2-bench" / "data"
if "TAU2_DATA_DIR" not in os.environ and _SUBMODULE_DATA.is_dir():
    os.environ["TAU2_DATA_DIR"] = str(_SUBMODULE_DATA)

_data_dir = os.environ.get("TAU2_DATA_DIR")
# None when domain data is missing (submodule not initialised).
TAU2_DATA_DIR: Path | None = Path(_data_dir) if _data_dir and Path(_data_dir).is_dir() else None
