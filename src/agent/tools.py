"""Tools the ADK agent can call: retrieve moments and build a playable clip URL."""

from __future__ import annotations

from typing import Any

from ..config import Config
from ..embedder import Embedder
from ..gcs_utils import signed_clip_url
from ..vector_store import VectorStore

_cfg: Config | None = None
_embedder: Embedder | None = None
_store: VectorStore | None = None


def _ensure_loaded() -> None:
    global _cfg, _embedder, _store
    if _cfg is None:
        _cfg = Config.load()
    if _embedder is None:
        _embedder = Embedder(_cfg)
    if _store is None:
        _store = VectorStore(_cfg)


def retrieve_moments(query: str, top_k: int = 5, video_id: str = "") -> dict[str, Any]:
    """Search the moment vector index.

    Args:
        query: Natural language description of the moment to find.
        top_k: How many moments to return (1-20).
        video_id: If non-empty, restrict the search to a single video_id.

    Returns:
        A dict with key "moments", each entry having: moment_id, video_id,
        start_seconds, end_seconds, title, description, distance.
    """
    _ensure_loaded()
    assert _embedder is not None and _store is not None
    top_k = max(1, min(int(top_k), 20))
    vec = _embedder.embed_query(query)
    hits = _store.query(query_vector=vec, top_k=top_k, video_id=video_id or None)
    out: list[dict[str, Any]] = []
    for h in hits:
        m = h.get("moment", {})
        out.append(
            {
                "moment_id": h.get("moment_id"),
                "video_id": h.get("video_id"),
                "gcs_uri": h.get("gcs_uri"),
                "start_seconds": m.get("start_seconds"),
                "end_seconds": m.get("end_seconds"),
                "title": m.get("title"),
                "description": m.get("description"),
                "scene_type": m.get("scene_type"),
                "entities": m.get("entities"),
                "actions": m.get("actions"),
                "location": m.get("location"),
                "dialogue_summary": m.get("dialogue_summary"),
                "mood": m.get("mood"),
                "keywords": m.get("keywords"),
                "distance": h.get("distance"),
            }
        )
    return {"moments": out}


def get_clip_url(
    gcs_uri: str,
    start_seconds: int,
    end_seconds: int,
    expires_minutes: int = 60,
) -> dict[str, str]:
    """Generate a signed HTTPS URL for a moment clip.

    Args:
        gcs_uri: gs:// URI of the source video.
        start_seconds: clip start (inclusive).
        end_seconds: clip end (inclusive).
        expires_minutes: how long the signed URL stays valid (default 60).

    Returns:
        Dict with the playable URL.
    """
    _ensure_loaded()
    assert _cfg is not None
    url = signed_clip_url(_cfg, gcs_uri, int(start_seconds), int(end_seconds), int(expires_minutes))
    return {"url": url}
