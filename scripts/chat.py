"""CLI: REPL chat with the ADK agent."""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from google.adk.runners import InMemoryRunner
from google.genai import types
from rich.console import Console
from rich.markdown import Markdown

from src.agent.agent import build_agent

console = Console()


async def _chat() -> None:
    agent = build_agent()
    runner = InMemoryRunner(agent=agent, app_name="video_moments_rag")
    session = await runner.session_service.create_session(
        app_name="video_moments_rag", user_id="local"
    )
    console.print("[bold cyan]video-moments-rag chat[/bold cyan]  (Ctrl+C to exit)")
    while True:
        try:
            user = console.input("[bold green]you> [/bold green]").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\nbye.")
            return
        if not user:
            continue
        message = types.Content(role="user", parts=[types.Part.from_text(text=user)])
        chunks: list[str] = []
        async for event in runner.run_async(
            user_id="local", session_id=session.id, new_message=message
        ):
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        chunks.append(part.text)
        reply = "".join(chunks).strip()
        if reply:
            console.print(Markdown(reply))
        else:
            console.print("[dim](no text reply)[/dim]")


if __name__ == "__main__":
    asyncio.run(_chat())
