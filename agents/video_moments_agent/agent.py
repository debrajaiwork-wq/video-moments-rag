"""Re-exports the agent for `adk web` / `adk run` discovery.

ADK expects an `agents_dir/<name>/agent.py` exposing `root_agent` at the module
level. The actual agent is built in `src/agent/agent.py`; this thin wrapper
just makes the project root importable and re-exports it.
"""
from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.agent.agent import root_agent  # noqa: E402

__all__ = ["root_agent"]
