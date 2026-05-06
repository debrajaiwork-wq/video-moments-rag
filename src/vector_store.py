"""BigQuery-backed vector store using the VECTOR_SEARCH function.

Cheaper than Vertex AI Vector Search for low-volume / bursty workloads —
truly serverless, pay-per-query, no idle endpoint cost. Trade-off: queries
take a couple of seconds (vs. <100ms for a deployed Vector Search index).
"""
from __future__ import annotations

import json
import uuid
from typing import Any, Dict, List, Optional

from google.api_core import exceptions as gax_exceptions
from google.cloud import bigquery

from .config import Config

_SCHEMA = [
    bigquery.SchemaField("moment_id", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("video_id", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("gcs_uri", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("moment_json", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("embedding", "FLOAT64", mode="REPEATED"),
]


def make_moment_id(video_id: str, start: int, end: int) -> str:
    short = uuid.uuid4().hex[:6]
    return f"{video_id}__{start:07d}_{end:07d}__{short}"


class VectorStore:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.client = bigquery.Client(project=cfg.project_id, location=cfg.location)
        self.dataset_ref = bigquery.DatasetReference(cfg.project_id, cfg.bq_dataset)
        self.table_ref = self.dataset_ref.table(cfg.bq_moments_table)
        self.full_table_id = (
            f"{cfg.project_id}.{cfg.bq_dataset}.{cfg.bq_moments_table}"
        )

    # ---------- setup ----------

    def ensure_table(self) -> None:
        try:
            self.client.get_dataset(self.dataset_ref)
        except gax_exceptions.NotFound:
            ds = bigquery.Dataset(self.dataset_ref)
            ds.location = self.cfg.location
            self.client.create_dataset(ds)
            print(f"  created dataset {self.cfg.project_id}.{self.cfg.bq_dataset}")
        try:
            self.client.get_table(self.table_ref)
            print(f"  table already exists: {self.full_table_id}")
        except gax_exceptions.NotFound:
            table = bigquery.Table(self.table_ref, schema=_SCHEMA)
            self.client.create_table(table)
            print(f"  created table {self.full_table_id}")

    # ---------- writes ----------

    def upsert(
        self,
        moments: List[Dict[str, Any]],
        embeddings: List[List[float]],
        video_id: str,
        gcs_uri: str,
    ) -> List[str]:
        if len(moments) != len(embeddings):
            raise ValueError("moments / embeddings length mismatch")
        rows: List[Dict[str, Any]] = []
        ids: List[str] = []
        for m, vec in zip(moments, embeddings):
            mid = make_moment_id(video_id, m["start_seconds"], m["end_seconds"])
            ids.append(mid)
            rows.append(
                {
                    "moment_id": mid,
                    "video_id": video_id,
                    "gcs_uri": gcs_uri,
                    "moment_json": json.dumps(m, ensure_ascii=False),
                    "embedding": [float(x) for x in vec],
                }
            )
        # Load job (not streaming insert) — rows are immediately queryable.
        job_config = bigquery.LoadJobConfig(
            schema=_SCHEMA,
            write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
            source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
        )
        load_job = self.client.load_table_from_json(
            rows, self.table_ref, job_config=job_config
        )
        load_job.result()
        return ids

    # ---------- reads ----------

    def query(
        self,
        query_vector: List[float],
        top_k: int = 5,
        video_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        if video_id:
            base_clause = (
                f"(SELECT * FROM `{self.full_table_id}` WHERE video_id = @video_id)"
            )
        else:
            base_clause = f"TABLE `{self.full_table_id}`"
        sql = f"""
        SELECT
          base.moment_id   AS moment_id,
          base.video_id    AS video_id,
          base.gcs_uri     AS gcs_uri,
          base.moment_json AS moment_json,
          distance
        FROM VECTOR_SEARCH(
          {base_clause},
          'embedding',
          (SELECT @q AS embedding),
          top_k => @top_k,
          distance_type => 'COSINE'
        )
        ORDER BY distance ASC
        """
        params: List[bigquery.ScalarQueryParameter | bigquery.ArrayQueryParameter] = [
            bigquery.ArrayQueryParameter("q", "FLOAT64", [float(x) for x in query_vector]),
            bigquery.ScalarQueryParameter("top_k", "INT64", int(top_k)),
        ]
        if video_id:
            params.append(
                bigquery.ScalarQueryParameter("video_id", "STRING", video_id)
            )
        job = self.client.query(
            sql, job_config=bigquery.QueryJobConfig(query_parameters=params)
        )
        results: List[Dict[str, Any]] = []
        for row in job.result():
            mj = row["moment_json"]
            moment = json.loads(mj) if isinstance(mj, str) else mj
            results.append(
                {
                    "moment_id": row["moment_id"],
                    "video_id": row["video_id"],
                    "gcs_uri": row["gcs_uri"],
                    "moment": moment,
                    "distance": float(row["distance"]),
                }
            )
        return results
