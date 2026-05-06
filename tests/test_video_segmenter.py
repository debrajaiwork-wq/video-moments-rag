"""Tests for src.video_segmenter.split_segments — pure logic, no GCP."""
from __future__ import annotations

from src.video_segmenter import split_segments


def test_short_video_returns_single_segment() -> None:
    assert split_segments(300, segment_length=600) == [(0, 300)]


def test_exact_segment_length_returns_single_segment() -> None:
    assert split_segments(600, segment_length=600) == [(0, 600)]


def test_segment_length_none_returns_single_segment() -> None:
    assert split_segments(5000, segment_length=None) == [(0, 5000)]


def test_long_video_splits_into_multiple_no_gaps_no_overlaps() -> None:
    duration = 1500
    segments = split_segments(duration, segment_length=600)
    # 1500 / 3 = 500 < 600, so 3 parts
    assert len(segments) == 3
    # starts at 0, ends exactly at duration
    assert segments[0][0] == 0
    assert segments[-1][1] == duration
    # contiguous: each segment's end == next segment's start
    for prev, curr in zip(segments, segments[1:]):
        assert prev[1] == curr[0]


def test_overlap_extends_non_final_segments() -> None:
    duration = 1500
    overlap = 30
    segments = split_segments(duration, segment_length=600, overlap=overlap)
    # final segment still ends exactly at duration
    assert segments[-1][1] == duration
    # at least one non-final segment was extended by overlap
    base = duration // len(segments)
    assert any((end - start) > base for start, end in segments[:-1])


def test_integer_division_tail_is_covered() -> None:
    # 3700 // 7 = 528 -> last segment would otherwise leave 4s uncovered.
    duration = 3700
    segments = split_segments(duration, segment_length=600)
    assert segments[-1][1] == duration
