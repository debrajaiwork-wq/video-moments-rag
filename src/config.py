"""Central configuration loaded from environment / .env."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")


def _required(name: str) -> str:
    val = os.environ.get(name)
    if not val:
        raise RuntimeError(f"Missing required env var: {name}")
    return val


@dataclass(frozen=True)
class Config:
    project_id: str
    location: str
    gcs_bucket: str
    gcs_video_prefix: str
    gcs_output_prefix: str
    gemini_model: str
    embedding_model: str
    embedding_dim: int
    bq_dataset: str
    bq_moments_table: str
    output_dir: Path
    project_root: Path

    @classmethod
    def load(cls) -> Config:
        return cls(
            project_id=_required("GCP_PROJECT_ID"),
            location=os.environ.get("GCP_LOCATION", "us-central1"),
            gcs_bucket=_required("GCS_BUCKET"),
            gcs_video_prefix=os.environ.get("GCS_VIDEO_PREFIX", "videos"),
            gcs_output_prefix=os.environ.get("GCS_OUTPUT_PREFIX", "moments"),
            gemini_model=os.environ.get("GEMINI_MODEL", "gemini-2.5-pro"),
            embedding_model=os.environ.get("EMBEDDING_MODEL", "text-embedding-005"),
            embedding_dim=int(os.environ.get("EMBEDDING_DIM", "768")),
            bq_dataset=os.environ.get("BQ_DATASET", "moments"),
            bq_moments_table=os.environ.get("BQ_MOMENTS_TABLE", "moments"),
            output_dir=PROJECT_ROOT / os.environ.get("OUTPUT_DIR", "output"),
            project_root=PROJECT_ROOT,
        )
