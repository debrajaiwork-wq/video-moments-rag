"""LangChain agent that answers moment queries via RAG."""

from __future__ import annotations

import logging
import os

from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_google_vertexai import ChatVertexAI

from ..config import Config
from .tools import get_clip_url, retrieve_moments

logger = logging.getLogger(__name__)


def _get_langfuse_handler():
    """Create Langfuse callback handler if keys are configured."""
    public_key = os.environ.get("LANGFUSE_PUBLIC_KEY")
    secret_key = os.environ.get("LANGFUSE_SECRET_KEY")
    if not public_key or not secret_key:
        logger.info("Langfuse keys not set — observability disabled.")
        return None
    try:
        from langfuse.langchain import CallbackHandler

        handler = CallbackHandler()
        logger.info("Langfuse observability enabled.")
        return handler
    except ImportError:
        logger.warning("langfuse package not installed — observability disabled.")
        return None

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


def build_agent(
    cfg: Config | None = None,
) -> tuple[AgentExecutor, list]:
    """Build the LangChain agent with optional Langfuse observability.

    Returns:
        (executor, callbacks) — pass callbacks into executor.invoke(..., config={"callbacks": callbacks})
    """
    cfg = cfg or Config.load()

    llm = ChatVertexAI(
        model_name=cfg.gemini_model,
        project=cfg.project_id,
        location=cfg.location,
        temperature=0,
    )

    tools = [retrieve_moments, get_clip_url]

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", INSTRUCTIONS),
            MessagesPlaceholder("chat_history", optional=True),
            ("human", "{input}"),
            MessagesPlaceholder("agent_scratchpad"),
        ]
    )

    agent = create_tool_calling_agent(llm, tools, prompt)
    executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=False,
        handle_parsing_errors=True,
        max_iterations=10,
    )

    # Langfuse observability
    callbacks = []
    langfuse_handler = _get_langfuse_handler()
    if langfuse_handler:
        callbacks.append(langfuse_handler)

    return executor, callbacks
