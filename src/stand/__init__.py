"""Testbed: τ-bench agents as black boxes.

Runs before any tau2 import: tau2 reads env vars and logs at DEBUG on import.
"""

import os
import sys

from dotenv import load_dotenv
from loguru import logger

load_dotenv()

logger.remove()
logger.add(sys.stderr, level=os.getenv("STAND_LOG_LEVEL", "WARNING"))
