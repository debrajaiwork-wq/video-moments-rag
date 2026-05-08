"""Social media signal fetcher — YouTube + Reddit buzz for videos.

Used as a ranking boost in RAG retrieval. When social signals are available,
the agent can highlight moments that align with what people are talking about.
"""

from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass, field
from typing import Any

import httpx

logger = logging.getLogger(__name__)

_YT_API_BASE = "https://www.googleapis.com/youtube/v3"
_REDDIT_SEARCH = "https://www.reddit.com/search.json"
_TIMEOUT = 10


@dataclass
class SocialSignals:
    """Aggregated social buzz for a video."""

    source: str  # "youtube" | "reddit" | "combined"
    video_title: str = ""
    view_count: int = 0
    like_count: int = 0
    comment_count: int = 0
    top_comments: list[str] = field(default_factory=list)
    trending_topics: list[str] = field(default_factory=list)
    sentiment_hint: str = ""  # "positive", "negative", "mixed", "unknown"
    raw: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "video_title": self.video_title,
            "view_count": self.view_count,
            "like_count": self.like_count,
            "comment_count": self.comment_count,
            "top_comments": self.top_comments[:5],
            "trending_topics": self.trending_topics,
            "sentiment_hint": self.sentiment_hint,
        }


def _extract_youtube_id(query: str) -> str | None:
    """Try to extract a YouTube video ID from a query string or URL."""
    patterns = [
        r"(?:youtube\.com/watch\?v=|youtu\.be/)([\w-]{11})",
        r"^([\w-]{11})$",
    ]
    for p in patterns:
        m = re.search(p, query.strip())
        if m:
            return m.group(1)
    return None


def fetch_youtube_signals(
    query: str,
    api_key: str | None = None,
    max_comments: int = 10,
) -> SocialSignals | None:
    """Fetch YouTube stats + top comments for a video.

    Args:
        query: YouTube video ID, URL, or search term.
        api_key: YouTube Data API v3 key. Falls back to YOUTUBE_API_KEY env var.
        max_comments: Max number of top comments to fetch.

    Returns:
        SocialSignals or None if the API call fails.
    """
    api_key = api_key or os.environ.get("YOUTUBE_API_KEY")
    if not api_key:
        logger.info("YOUTUBE_API_KEY not set — skipping YouTube signals.")
        return None

    video_id = _extract_youtube_id(query)
    try:
        with httpx.Client(timeout=_TIMEOUT) as client:
            # If no video ID, search first
            if not video_id:
                resp = client.get(
                    f"{_YT_API_BASE}/search",
                    params={
                        "part": "snippet",
                        "q": query,
                        "type": "video",
                        "maxResults": 1,
                        "key": api_key,
                    },
                )
                resp.raise_for_status()
                items = resp.json().get("items", [])
                if not items:
                    return None
                video_id = items[0]["id"]["videoId"]

            # Get video stats
            resp = client.get(
                f"{_YT_API_BASE}/videos",
                params={
                    "part": "snippet,statistics",
                    "id": video_id,
                    "key": api_key,
                },
            )
            resp.raise_for_status()
            items = resp.json().get("items", [])
            if not items:
                return None

            video = items[0]
            snippet = video.get("snippet", {})
            stats = video.get("statistics", {})

            # Get top comments
            comments: list[str] = []
            try:
                resp = client.get(
                    f"{_YT_API_BASE}/commentThreads",
                    params={
                        "part": "snippet",
                        "videoId": video_id,
                        "maxResults": max_comments,
                        "order": "relevance",
                        "key": api_key,
                    },
                )
                resp.raise_for_status()
                for item in resp.json().get("items", []):
                    text = (
                        item.get("snippet", {})
                        .get("topLevelComment", {})
                        .get("snippet", {})
                        .get("textDisplay", "")
                    )
                    if text:
                        comments.append(text[:200])  # Truncate long comments
            except httpx.HTTPError:
                logger.warning("Could not fetch YouTube comments.")

            return SocialSignals(
                source="youtube",
                video_title=snippet.get("title", ""),
                view_count=int(stats.get("viewCount", 0)),
                like_count=int(stats.get("likeCount", 0)),
                comment_count=int(stats.get("commentCount", 0)),
                top_comments=comments,
                trending_topics=snippet.get("tags", [])[:10],
                sentiment_hint=_guess_sentiment(comments),
                raw={"video_id": video_id, "channel": snippet.get("channelTitle", "")},
            )

    except httpx.HTTPError as e:
        logger.warning("YouTube API error: %s", e)
        return None


def fetch_reddit_signals(
    query: str,
    max_posts: int = 5,
    max_comments: int = 10,
) -> SocialSignals | None:
    """Search Reddit for discussions about a video/topic.

    Uses Reddit's public JSON API (no auth required).

    Args:
        query: Search term (video title, topic, etc.).
        max_posts: Number of Reddit posts to scan.
        max_comments: Total comments to collect across posts.

    Returns:
        SocialSignals or None if the API call fails.
    """
    try:
        headers = {"User-Agent": "video-moments-rag/1.0"}
        with httpx.Client(timeout=_TIMEOUT, headers=headers) as client:
            resp = client.get(
                _REDDIT_SEARCH,
                params={
                    "q": query,
                    "sort": "relevance",
                    "limit": max_posts,
                    "type": "link",
                },
            )
            resp.raise_for_status()
            posts = resp.json().get("data", {}).get("children", [])

            if not posts:
                return None

            total_upvotes = 0
            total_comments = 0
            top_comments: list[str] = []
            topics: list[str] = []

            for post in posts:
                data = post.get("data", {})
                total_upvotes += data.get("ups", 0)
                total_comments += data.get("num_comments", 0)
                title = data.get("title", "")
                if title:
                    topics.append(title[:100])

                # Fetch top comments from each post
                if len(top_comments) < max_comments:
                    permalink = data.get("permalink", "")
                    if permalink:
                        try:
                            comment_resp = client.get(
                                f"https://www.reddit.com{permalink}.json",
                                params={"limit": 3, "sort": "best"},
                            )
                            comment_resp.raise_for_status()
                            comment_data = comment_resp.json()
                            if len(comment_data) > 1:
                                for c in comment_data[1].get("data", {}).get("children", []):
                                    body = c.get("data", {}).get("body", "")
                                    if body and len(top_comments) < max_comments:
                                        top_comments.append(body[:200])
                        except httpx.HTTPError:
                            pass

            return SocialSignals(
                source="reddit",
                view_count=0,
                like_count=total_upvotes,
                comment_count=total_comments,
                top_comments=top_comments,
                trending_topics=topics,
                sentiment_hint=_guess_sentiment(top_comments),
            )

    except httpx.HTTPError as e:
        logger.warning("Reddit API error: %s", e)
        return None


def fetch_social_signals(query: str) -> dict[str, Any]:
    """Fetch and combine social signals from all sources.

    Args:
        query: Video title, topic, or YouTube URL/ID.

    Returns:
        Dict with combined signals from YouTube + Reddit.
    """
    results: dict[str, Any] = {"query": query, "sources": []}

    yt = fetch_youtube_signals(query)
    if yt:
        results["sources"].append(yt.to_dict())

    reddit = fetch_reddit_signals(query)
    if reddit:
        results["sources"].append(reddit.to_dict())

    # Build combined summary
    all_comments = []
    all_topics = []
    total_engagement = 0
    for src in results["sources"]:
        all_comments.extend(src.get("top_comments", []))
        all_topics.extend(src.get("trending_topics", []))
        total_engagement += src.get("view_count", 0) + src.get("like_count", 0)

    results["combined"] = {
        "total_engagement": total_engagement,
        "top_comments": all_comments[:10],
        "trending_topics": list(dict.fromkeys(all_topics))[:10],  # deduplicated
        "sentiment": _guess_sentiment(all_comments),
        "has_signals": len(results["sources"]) > 0,
    }

    return results


def _guess_sentiment(comments: list[str]) -> str:
    """Simple keyword-based sentiment hint.

    Not meant to be accurate — just gives the agent a rough signal.
    A proper implementation would use a sentiment model.
    """
    if not comments:
        return "unknown"

    positive_words = {"love", "great", "amazing", "funny", "best", "awesome", "hilarious",
                      "brilliant", "perfect", "fantastic", "lol", "haha", "classic"}
    negative_words = {"hate", "worst", "boring", "terrible", "awful", "bad", "cringe",
                      "disappointing", "overrated", "stupid"}

    pos_count = 0
    neg_count = 0
    text = " ".join(comments).lower()
    for w in positive_words:
        if w in text:
            pos_count += 1
    for w in negative_words:
        if w in text:
            neg_count += 1

    if pos_count > neg_count * 2:
        return "positive"
    if neg_count > pos_count * 2:
        return "negative"
    if pos_count > 0 or neg_count > 0:
        return "mixed"
    return "unknown"
