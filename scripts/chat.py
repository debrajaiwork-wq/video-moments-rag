"""CLI: REPL chat with the LangChain agent."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rich.console import Console
from rich.markdown import Markdown

from src.agent.agent import build_agent

console = Console()


def _chat() -> None:
    executor, callbacks = build_agent()
    chat_history: list = []
    if callbacks:
        console.print("[bold cyan]video-moments-rag chat[/bold cyan]  [green](Langfuse ON)[/green]  (Ctrl+C to exit)")
    else:
        console.print("[bold cyan]video-moments-rag chat[/bold cyan]  (Ctrl+C to exit)")
    while True:
        try:
            user = console.input("[bold green]you> [/bold green]").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\nbye.")
            return
        if not user:
            continue
        result = executor.invoke(
            {"input": user, "chat_history": chat_history},
            config={"callbacks": callbacks} if callbacks else {},
        )
        reply = result.get("output", "").strip()
        if reply:
            console.print(Markdown(reply))
        else:
            console.print("[dim](no text reply)[/dim]")
        # Keep conversation history for multi-turn
        chat_history.append({"role": "user", "content": user})
        chat_history.append({"role": "assistant", "content": reply})


if __name__ == "__main__":
    _chat()
