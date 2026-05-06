"""Shared test fixtures.

Sets fake env vars so `Config.load()` succeeds without a real .env, and adds
the project root to sys.path so `import src.*` works whether pytest is run
from the project root or from `tests/`.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture(autouse=True)
def _fake_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GCP_PROJECT_ID", "fake-project")
    monkeypatch.setenv("GCP_LOCATION", "us-central1")
    monkeypatch.setenv("GCS_BUCKET", "fake-bucket")
    monkeypatch.setenv("GEMINI_MODEL", "gemini-2.5-pro")
    monkeypatch.setenv("EMBEDDING_MODEL", "text-embedding-005")
    monkeypatch.setenv("EMBEDDING_DIM", "768")
