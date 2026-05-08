"""Vertex AI text embeddings via LangChain."""

from __future__ import annotations

from typing import Any

from langchain_google_vertexai import VertexAIEmbeddings

from .config import Config


def moment_to_text(moment: dict[str, Any]) -> str:
    """Flatten a moment dict into a single retrievable text blob."""
    parts: list[str] = []
    if title := moment.get("title"):
        parts.append(f"Title: {title}")
    if desc := moment.get("description"):
        parts.append(f"Description: {desc}")
    if loc := moment.get("location"):
        parts.append(f"Location: {loc}")
    if mood := moment.get("mood"):
        parts.append(f"Mood: {mood}")
    if scene := moment.get("scene_type"):
        parts.append(f"Scene: {scene}")
    if dlg := moment.get("dialogue_summary"):
        parts.append(f"Dialogue: {dlg}")
    if ents := moment.get("entities"):
        parts.append(f"Entities: {', '.join(ents)}")
    if acts := moment.get("actions"):
        parts.append(f"Actions: {', '.join(acts)}")
    if kws := moment.get("keywords"):
        parts.append(f"Keywords: {', '.join(kws)}")
    return "\n".join(parts)


class Embedder:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.model = VertexAIEmbeddings(
            model_name=cfg.embedding_model,
            project=cfg.project_id,
            location=cfg.location,
        )

    def embed(self, texts: list[str], task_type: str = "RETRIEVAL_DOCUMENT") -> list[list[float]]:
        if not texts:
            return []
        return self.model.embed_documents(texts)

    def embed_query(self, query: str) -> list[float]:
        return self.model.embed_query(query)
