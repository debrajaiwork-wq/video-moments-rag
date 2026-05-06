"""Tests for src.embedder.moment_to_text — pure formatting, no GCP."""
from __future__ import annotations

from src.embedder import moment_to_text


def test_moment_to_text_includes_all_populated_fields() -> None:
    moment = {
        "title": "T",
        "description": "D",
        "scene_type": "dialogue",
        "entities": ["Alice", "Bob"],
        "actions": ["walk", "talk"],
        "location": "Cafe",
        "dialogue_summary": "DS",
        "mood": "calm",
        "keywords": ["k1", "k2"],
    }
    text = moment_to_text(moment)
    assert "Title: T" in text
    assert "Description: D" in text
    assert "Scene: dialogue" in text
    assert "Entities: Alice, Bob" in text
    assert "Actions: walk, talk" in text
    assert "Location: Cafe" in text
    assert "Dialogue: DS" in text
    assert "Mood: calm" in text
    assert "Keywords: k1, k2" in text


def test_moment_to_text_skips_empty_fields() -> None:
    text = moment_to_text({"title": "Only", "entities": [], "description": ""})
    # Only the populated field shows up; empty strings/lists are dropped.
    assert text == "Title: Only"


def test_moment_to_text_handles_missing_keys() -> None:
    # Should not raise on a partial moment dict.
    text = moment_to_text({"keywords": ["solo"]})
    assert text == "Keywords: solo"
