"""Tests for src.social — fully mocked HTTP calls."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.social import (
    SocialSignals,
    _extract_youtube_id,
    _guess_sentiment,
    fetch_reddit_signals,
    fetch_social_signals,
    fetch_youtube_signals,
)

# ── YouTube ID extraction ──


@pytest.mark.parametrize(
    "input_str, expected",
    [
        ("https://www.youtube.com/watch?v=dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ("https://youtu.be/dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ("dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ("funny cat video", None),
        ("", None),
    ],
)
def test_extract_youtube_id(input_str: str, expected: str | None) -> None:
    assert _extract_youtube_id(input_str) == expected


# ── Sentiment heuristic ──


def test_sentiment_positive() -> None:
    comments = ["This is amazing!", "Love this scene, hilarious!", "Best episode ever"]
    assert _guess_sentiment(comments) == "positive"


def test_sentiment_negative() -> None:
    comments = ["Worst episode", "So boring and terrible", "Awful writing, hate it"]
    assert _guess_sentiment(comments) == "negative"


def test_sentiment_mixed() -> None:
    comments = ["Great scene!", "Terrible ending"]
    assert _guess_sentiment(comments) == "mixed"


def test_sentiment_unknown_empty() -> None:
    assert _guess_sentiment([]) == "unknown"


# ── SocialSignals dataclass ──


def test_social_signals_to_dict() -> None:
    signals = SocialSignals(
        source="youtube",
        video_title="Test Video",
        view_count=1000,
        like_count=50,
        comment_count=10,
        top_comments=["Great!", "Awesome!"],
        trending_topics=["funny"],
        sentiment_hint="positive",
    )
    d = signals.to_dict()
    assert d["source"] == "youtube"
    assert d["view_count"] == 1000
    assert d["like_count"] == 50
    assert len(d["top_comments"]) == 2
    assert "raw" not in d  # raw should not be in to_dict output


# ── YouTube fetch (mocked) ──


def test_youtube_signals_no_api_key() -> None:
    """Returns None when no API key is available."""
    with patch.dict("os.environ", {}, clear=True):
        result = fetch_youtube_signals("test query", api_key=None)
    assert result is None


@patch("src.social.httpx.Client")
def test_youtube_signals_with_video_id(mock_client_cls: MagicMock) -> None:
    """Fetches stats and comments for a known video ID."""
    mock_client = MagicMock()
    mock_client_cls.return_value.__enter__ = MagicMock(return_value=mock_client)
    mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)

    # Video stats response
    video_resp = MagicMock()
    video_resp.json.return_value = {
        "items": [
            {
                "snippet": {"title": "Big Bang Theory Clip", "tags": ["comedy", "sheldon"]},
                "statistics": {"viewCount": "5000000", "likeCount": "50000", "commentCount": "2000"},
            }
        ]
    }

    # Comments response
    comments_resp = MagicMock()
    comments_resp.json.return_value = {
        "items": [
            {"snippet": {"topLevelComment": {"snippet": {"textDisplay": "So funny!"}}}},
            {"snippet": {"topLevelComment": {"snippet": {"textDisplay": "Classic Sheldon"}}}},
        ]
    }

    mock_client.get.side_effect = [video_resp, comments_resp]

    result = fetch_youtube_signals("dQw4w9WgXcQ", api_key="fake-key")

    assert result is not None
    assert result.source == "youtube"
    assert result.view_count == 5000000
    assert result.like_count == 50000
    assert len(result.top_comments) == 2
    assert "comedy" in result.trending_topics


# ── Reddit fetch (mocked) ──


@patch("src.social.httpx.Client")
def test_reddit_signals_returns_data(mock_client_cls: MagicMock) -> None:
    """Fetches Reddit posts and comments."""
    mock_client = MagicMock()
    mock_client_cls.return_value.__enter__ = MagicMock(return_value=mock_client)
    mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)

    # Search response
    search_resp = MagicMock()
    search_resp.json.return_value = {
        "data": {
            "children": [
                {
                    "data": {
                        "title": "Big Bang Theory funniest moments",
                        "ups": 1500,
                        "num_comments": 200,
                        "permalink": "/r/television/comments/abc123/test/",
                    }
                }
            ]
        }
    }

    # Comments response
    comment_resp = MagicMock()
    comment_resp.json.return_value = [
        {},
        {
            "data": {
                "children": [
                    {"data": {"body": "Bazinga! Best show ever"}},
                    {"data": {"body": "Sheldon is hilarious"}},
                ]
            }
        },
    ]

    mock_client.get.side_effect = [search_resp, comment_resp]

    result = fetch_reddit_signals("big bang theory funny")

    assert result is not None
    assert result.source == "reddit"
    assert result.like_count == 1500
    assert result.comment_count == 200
    assert len(result.top_comments) == 2


@patch("src.social.httpx.Client")
def test_reddit_signals_no_results(mock_client_cls: MagicMock) -> None:
    """Returns None when Reddit has no results."""
    mock_client = MagicMock()
    mock_client_cls.return_value.__enter__ = MagicMock(return_value=mock_client)
    mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)

    resp = MagicMock()
    resp.json.return_value = {"data": {"children": []}}
    mock_client.get.return_value = resp

    result = fetch_reddit_signals("something nobody posted about ever xyz123")
    assert result is None


# ── Combined fetch ──


@patch("src.social.fetch_reddit_signals")
@patch("src.social.fetch_youtube_signals")
def test_fetch_social_signals_combines_sources(
    mock_yt: MagicMock, mock_reddit: MagicMock
) -> None:
    """Combines YouTube + Reddit into a single result."""
    mock_yt.return_value = SocialSignals(
        source="youtube",
        view_count=1000000,
        like_count=10000,
        top_comments=["Amazing!"],
        trending_topics=["comedy"],
        sentiment_hint="positive",
    )
    mock_reddit.return_value = SocialSignals(
        source="reddit",
        like_count=500,
        comment_count=50,
        top_comments=["Great show"],
        trending_topics=["big bang theory"],
        sentiment_hint="positive",
    )

    result = fetch_social_signals("big bang theory")

    assert len(result["sources"]) == 2
    assert result["combined"]["total_engagement"] == 1000000 + 10000 + 500
    assert result["combined"]["has_signals"] is True
    assert len(result["combined"]["top_comments"]) == 2


@patch("src.social.fetch_reddit_signals", return_value=None)
@patch("src.social.fetch_youtube_signals", return_value=None)
def test_fetch_social_signals_no_sources(mock_yt: MagicMock, mock_reddit: MagicMock) -> None:
    """Returns empty when no sources available."""
    result = fetch_social_signals("unknown video")
    assert result["combined"]["has_signals"] is False
    assert result["combined"]["total_engagement"] == 0
