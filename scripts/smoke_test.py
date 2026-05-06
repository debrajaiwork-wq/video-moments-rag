"""Staging smoke test — verifies GCP connectivity without ingesting real video.

Checks:
  1. BigQuery dataset and moments table exist and are queryable
  2. GCS bucket is accessible
  3. Embedding model responds
  4. Critical modules import cleanly

Exit 0 on success, 1 on any failure.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import Config


def check_bigquery(cfg: Config) -> None:
    from google.cloud import bigquery

    client = bigquery.Client(project=cfg.project_id)
    table_ref = f"{cfg.project_id}.{cfg.bq_dataset}.{cfg.bq_moments_table}"
    table = client.get_table(table_ref)
    print(f"  BigQuery table {table_ref} exists ({table.num_rows} rows)")


def check_gcs(cfg: Config) -> None:
    from google.cloud import storage

    client = storage.Client(project=cfg.project_id)
    bucket = client.get_bucket(cfg.gcs_bucket)
    print(f"  GCS bucket gs://{bucket.name} is accessible")


def check_embedding(cfg: Config) -> None:
    from google import genai

    client = genai.Client(vertexai=True, project=cfg.project_id, location=cfg.location)
    result = client.models.embed_content(
        model=cfg.embedding_model,
        contents=["smoke test"],
    )
    dim = len(result.embeddings[0].values)
    print(f"  Embedding model {cfg.embedding_model} responded ({dim}-dim vector)")


def check_imports() -> None:
    import importlib

    for mod in [
        "src.vector_store",
        "src.extractor",
        "src.embedder",
        "src.agent.tools",
    ]:
        importlib.import_module(mod)
    print("  All critical modules import OK")


def main() -> int:
    print("Running staging smoke test...\n")
    cfg = Config.load()
    checks = [
        ("Imports", lambda: check_imports()),
        ("BigQuery", lambda: check_bigquery(cfg)),
        ("Cloud Storage", lambda: check_gcs(cfg)),
        ("Embeddings", lambda: check_embedding(cfg)),
    ]
    failed = []
    for name, fn in checks:
        try:
            fn()
        except Exception as e:
            print(f"  FAIL: {name} — {e}")
            failed.append(name)

    print()
    if failed:
        print(f"FAILED: {', '.join(failed)}")
        return 1
    print("All smoke tests passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
