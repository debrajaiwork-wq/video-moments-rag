"""Tests for src.agent.tools — fully mocked embedder + vector store."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from src.agent import tools


@pytest.fixture
def mocked_tools(monkeypatch: pytest.MonkeyPatch):
    fake_cfg = MagicMock()
    fake_embedder = MagicMock()
    fake_embedder.embed_query.return_value = [0.1] * 8
    fake_store = MagicMock()
    monkeypatch.setattr(tools, "_cfg", fake_cfg)
    monkeypatch.setattr(tools, "_embedder", fake_embedder)
    monkeypatch.setattr(tools, "_store", fake_store)
    return fake_cfg, fake_embedder, fake_store


def test_retrieve_moments_returns_flattened_hits(mocked_tools) -> None:
    _, fake_embedder, fake_store = mocked_tools
    fake_store.query.return_value = [
        {
            "moment_id": "vid1__0000000_0000030__abc123",
            "video_id": "vid1",
            "gcs_uri": "gs://b/vid1.mp4",
            "moment": {
                "start_seconds": 0,
                "end_seconds": 30,
                "title": "Opening",
                "description": "X happens.",
                "scene_type": "establishing",
                "entities": [],
                "actions": [],
                "location": "",
                "dialogue_summary": "",
                "mood": "",
                "keywords": [],
            },
            "distance": 0.42,
        }
    ]

    out = tools.retrieve_moments("opening scene", top_k=3)

    assert "moments" in out
    assert len(out["moments"]) == 1
    hit = out["moments"][0]
    assert hit["title"] == "Opening"
    assert hit["start_seconds"] == 0
    assert hit["end_seconds"] == 30
    assert hit["distance"] == pytest.approx(0.42)
    fake_embedder.embed_query.assert_called_once_with("opening scene")
    # video_id="" should pass None (not the empty string) to the store.
    fake_store.query.assert_called_once()
    kwargs = fake_store.query.call_args.kwargs
    assert kwargs["top_k"] == 3
    assert kwargs["video_id"] is None


def test_retrieve_moments_clamps_top_k(mocked_tools) -> None:
    _, _, fake_store = mocked_tools
    fake_store.query.return_value = []
    tools.retrieve_moments("q", top_k=999)
    assert fake_store.query.call_args.kwargs["top_k"] == 20

    fake_store.reset_mock()
    fake_store.query.return_value = []
    tools.retrieve_moments("q", top_k=0)
    assert fake_store.query.call_args.kwargs["top_k"] == 1


def test_retrieve_moments_passes_video_id(mocked_tools) -> None:
    _, _, fake_store = mocked_tools
    fake_store.query.return_value = []
    tools.retrieve_moments("q", top_k=5, video_id="vid42")
    assert fake_store.query.call_args.kwargs["video_id"] == "vid42"


def test_get_clip_url_calls_signed_url(monkeypatch: pytest.MonkeyPatch, mocked_tools) -> None:
    captured: dict = {}

    def fake_signed(cfg, gcs_uri, start, end, expires):
        captured.update(
            {"cfg": cfg, "uri": gcs_uri, "start": start, "end": end, "exp": expires}
        )
        return f"https://signed/{gcs_uri}#t={start},{end}"

    monkeypatch.setattr(tools, "signed_clip_url", fake_signed)
    out = tools.get_clip_url("gs://b/v.mp4", 10, 30, expires_minutes=15)

    assert out == {"url": "https://signed/gs://b/v.mp4#t=10,30"}
    assert captured["start"] == 10
    assert captured["end"] == 30
    assert captured["exp"] == 15
