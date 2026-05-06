"""CLI: ingest one video file or gs:// URI."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import typer

from src.config import Config
from src.ingest import ingest_video

app = typer.Typer(add_completion=False)


@app.command()
def main(
    source: str = typer.Argument(..., help="Local video path OR gs:// URI"),
    video_id: str = typer.Option(None, help="Override video_id (defaults to filename stem)"),
    segment_length: int = typer.Option(600, help="Max segment length in seconds for Gemini calls"),
    overlap: int = typer.Option(0, help="Seconds of overlap between segments"),
) -> None:
    cfg = Config.load()
    result = ingest_video(
        cfg,
        source=source,
        video_id=video_id,
        segment_length=segment_length,
        overlap=overlap,
    )
    print()
    print(f"Done. Ingested {result['num_moments']} moments for '{result['video_id']}'.")


if __name__ == "__main__":
    app()
