"""Re-exports the agent for discovery.

This thin wrapper just makes the project root importable and re-exports
the LangChain AgentExecutor.
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.agent.agent import build_agent  # noqa: E402

# Build the agent executor for external discovery.
agent_executor, langfuse_callbacks = build_agent()

__all__ = ["agent_executor", "langfuse_callbacks"]
