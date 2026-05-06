"""Smoke test for the Gemini extractor with a fully mocked client.

Verifies that segment-relative timestamps get offset back to source-video time.
"""
from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from src.config import Config
from src.extractor import MomentExtractor


def _fake_response(moments: list[dict]) -> MagicMock:
    resp = MagicMock()
    resp.text = json.dumps({"response": {"moments": moments}})
    return resp


@pytest.fixture
def extractor() -> MomentExtractor:
    cfg = Config.load()
    fake_client = MagicMock()
    with patch("src.extractor.genai.Client", return_value=fake_client):
        ext = MomentExtractor(cfg)
    # Hand the mock client back via attribute so tests can configure it.
    ext.client = fake_client  # type: ignore[assignment]
    return ext


def test_extract_segment_offsets_timestamps_to_source_video(extractor: MomentExtractor) -> None:
    extractor.client.models.generate_content.return_value = _fake_response(  # type: ignore[attr-defined]
        [
            {
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
            {
                "start_seconds": 30,
                "end_seconds": 90,
                "title": "Confrontation",
                "description": "Y happens.",
                "scene_type": "dialogue",
                "entities": ["Alice"],
                "actions": ["argue"],
                "location": "alley",
                "dialogue_summary": "",
                "mood": "tense",
                "keywords": ["argument"],
            },
        ]
    )

    out = extractor.extract_segment("gs://b/v.mp4", segment_start=600, segment_end=690)

    assert [m["start_seconds"] for m in out] == [600, 630]
    assert [m["end_seconds"] for m in out] == [630, 690]
    assert out[1]["title"] == "Confrontation"


def test_extract_video_iterates_segments(extractor: MomentExtractor) -> None:
    extractor.client.models.generate_content.side_effect = [  # type: ignore[attr-defined]
        _fake_response(
            [
                {
                    "start_seconds": 0,
                    "end_seconds": 60,
                    "title": "A",
                    "description": "",
                    "scene_type": "other",
                    "entities": [],
                    "actions": [],
                    "location": "",
                    "dialogue_summary": "",
                    "mood": "",
                    "keywords": [],
                }
            ]
        ),
        _fake_response(
            [
                {
                    "start_seconds": 0,
                    "end_seconds": 60,
                    "title": "B",
                    "description": "",
                    "scene_type": "other",
                    "entities": [],
                    "actions": [],
                    "location": "",
                    "dialogue_summary": "",
                    "mood": "",
                    "keywords": [],
                }
            ]
        ),
    ]

    out = extractor.extract_video("gs://b/v.mp4", segments=[(0, 60), (60, 120)])

    assert [m["start_seconds"] for m in out] == [0, 60]
    assert [m["title"] for m in out] == ["A", "B"]
