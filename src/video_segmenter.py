"""Probe a video and split it into time segments for Gemini calls.

Adapted from the Quickplay metadata-enrichment notebook's get_video_segments
but simplified for our single-pass moment extraction use case.
"""
from __future__ import annotations

from typing import List, Tuple

import ffmpeg

def probe_duration(video_uri: str) -> int:
    """Return integer-seconds duration for a local path or readable URL."""
    probe = ffmpeg.probe(video_uri)
    return round(float(probe["format"]["duration"]))


def split_segments(
    duration_seconds: int,
    segment_length: int = 600,
    overlap: int = 0,
) -> List[Tuple[int, int]]:
    """Split [0, duration) into chunks no longer than segment_length.

    The last chunk is stretched so coverage is exact (no leftover seconds).
    """
    if segment_length is None or duration_seconds <= segment_length:
        return [(0, duration_seconds)]

    parts = 2
    size = duration_seconds // parts
    while size >= segment_length:
        parts += 1
        size = duration_seconds // parts

    out: List[Tuple[int, int]] = []
    for i in range(parts):
        start = i * size
        end = start + size
        if end > duration_seconds:
            end = duration_seconds
        else:
            end = min(end + overlap, duration_seconds)
        out.append((start, end))
    if out and out[-1][1] < duration_seconds:
        out[-1] = (out[-1][0], duration_seconds)
    return out
