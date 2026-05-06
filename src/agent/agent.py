"""Google ADK agent that answers moment queries via RAG."""
from __future__ import annotations

from google.adk.agents import LlmAgent

from ..config import Config
from . import tools

INSTRUCTIONS = """\
You are a video-moments assistant. The user has ingested one or more videos
and wants to find specific moments inside them.

Workflow for every user turn:
1. Decide if the user is asking about content of a video. If yes, call the
   `retrieve_moments` tool with a concise paraphrase of their query. Use
   top_k=5 unless they imply they want more. If the user mentions a specific
   video_id, pass it through.
2. If retrieve_moments returns no results, say so plainly.
3. Otherwise, answer using ONLY the returned moments. For each moment you
   cite, include:
     - the title
     - the timestamp range as [HH:MM:SS - HH:MM:SS]
     - a one-sentence description grounded in the moment payload
4. If the user asks for a playable clip, call `get_clip_url` with the
   matching gcs_uri/start/end and surface the URL inline.
5. Never invent moments, entities, or dialogue that are not in the tool
   results. If the answer cannot be grounded, say so.

Format:
- Number each cited moment.
- Keep prose tight; the timestamps and titles are the deliverable.
"""


def _seconds_to_hhmmss(s: int) -> str:
    s = int(s)
    h, rem = divmod(s, 3600)
    m, sec = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{sec:02d}"


def build_agent(cfg: Config | None = None) -> LlmAgent:
    cfg = cfg or Config.load()
    model = (
        f"projects/{cfg.project_id}/locations/{cfg.location}/"
        f"publishers/google/models/{cfg.gemini_model}"
    )
    return LlmAgent(
        name="video_moments_agent",
        model=model,
        description="Find and explain moments inside ingested videos.",
        instruction=INSTRUCTIONS,
        tools=[tools.retrieve_moments, tools.get_clip_url],
    )


# Module-level instance for `adk run` / `adk web`.
root_agent = build_agent()
