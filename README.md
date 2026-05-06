# video-moments-rag

A small Google ADK + GCP project that ingests a video, extracts structured
"moments" with Gemini 2.5 Pro on Vertex AI, embeds them, stores them in
**BigQuery** (queried via `VECTOR_SEARCH`), and lets you query them through
an ADK agent CLI.

```
video ──► GCS ──► Gemini (segment-by-segment) ──► moments JSON
              ──► text-embedding-005 ──► BigQuery (VECTOR_SEARCH)
                                          ▲
                                          │
                              ADK agent (retrieve_moments,
                                         get_clip_url tools)
```

## Layout

```
video_moments_rag/
├── prompts/moments/{system_instruction,prompt}.txt
├── schemas/moments.json
├── scripts/
│   ├── setup_bq.py           # one-time: create BQ dataset + moments table
│   ├── ingest_video.py       # CLI: ingest one video
│   ├── chat.py               # CLI: chat with the ADK agent
│   └── cleanup_vector_search.py  # one-off: delete legacy Vertex AI VS resources
├── src/
│   ├── config.py
│   ├── gcs_utils.py
│   ├── video_segmenter.py
│   ├── extractor.py          # Gemini call w/ structured output
│   ├── embedder.py           # Vertex text embeddings
│   ├── vector_store.py       # BigQuery VECTOR_SEARCH wrapper
│   ├── ingest.py             # end-to-end pipeline
│   └── agent/
│       ├── tools.py          # retrieve_moments, get_clip_url
│       └── agent.py          # ADK LlmAgent
├── agents/                   # discovery dir for `adk web` / `adk run`
│   └── video_moments_agent/
│       ├── __init__.py
│       └── agent.py          # re-exports root_agent
├── tests/                    # mocked unit tests (no GCP needed)
├── .env.example
├── requirements.txt
└── requirements-dev.txt
```

## Setup

1. **Auth & gcloud**

   ```bash
   gcloud auth application-default login
   gcloud config set project project-0a83db49-ed06-47c9-be5
   gcloud services enable aiplatform.googleapis.com storage.googleapis.com bigquery.googleapis.com
   ```

2. **GCS bucket** — create a regional bucket in your `GCP_LOCATION`:

   ```bash
   gcloud storage buckets create gs://<your-bucket> --location=us-central1
   ```

3. **Python env**

   ```bash
   python -m venv .venv
   .venv\Scripts\activate     # Windows
   pip install -r requirements.txt
   ```

4. **`.env`** — copy `.env.example` to `.env` and set `GCS_BUCKET`. The
   `BQ_DATASET` and `BQ_MOMENTS_TABLE` defaults (`moments`/`moments`) are fine.

5. **Create the BigQuery vector store** (instant, no LRO):

   ```bash
   python scripts/setup_bq.py
   ```

## Usage

Ingest a local video file:

```bash
python scripts/ingest_video.py path/to/movie.mp4
```

Or a video already in GCS:

```bash
python scripts/ingest_video.py gs://your-bucket/videos/movie.mp4
```

Chat with the agent (Python REPL):

```bash
python scripts/chat.py
```

```
you> find moments where the protagonist confronts the villain
1. **The Rooftop Standoff** [00:42:11 - 00:43:50]
   ...
```

Or launch ADK's bundled web UI:

```bash
adk web agents
# visit http://localhost:8000 and pick "video_moments_agent"
```

## Tests

```bash
pip install -r requirements-dev.txt
pytest
```

Tests use mocked Gemini and BigQuery clients, so no GCP credentials or network
access are needed.

## Design notes

- **Why BigQuery instead of Vertex AI Vector Search?** BQ `VECTOR_SEARCH` is
  serverless and pay-per-query — no idle endpoint cost. Trade-off: queries
  take a couple of seconds (vs. <100ms for a deployed Vector Search index).
  Right answer for low-volume / bursty workloads; swap back if you need
  sub-second QPS at scale.
- **Segmenting**: long videos are probed via `ffmpeg.probe()` and split into
  ≤10-min chunks; Gemini is called per chunk, and segment-relative timestamps
  are offset back to source-video time before embedding.
- **Schema**: structured output via Vertex's `response_schema`. The schema is
  in `schemas/moments.json` and is the contract between the extractor and the
  embedder.
- **BigQuery table**: `moment_id, video_id, gcs_uri, moment_json, embedding`
  (an `ARRAY<FLOAT64>`). The full moment dict is stored as JSON in
  `moment_json` so we don't need a payload sidecar.
- **Agent tools**: `retrieve_moments(query, top_k, video_id)` runs a
  cosine-distance `VECTOR_SEARCH` and returns the top hits;
  `get_clip_url(gcs_uri, start, end)` mints a signed playback URL with a
  `#t=start,end` fragment.

## Costs (rough)

- **Gemini 2.5 Pro** on video: ~$0.005-0.02 per minute of input video (varies
  with prompt + output size).
- **text-embedding-005**: ~$0.0001 per 1k tokens — basically free for our use.
- **BigQuery storage**: ~$0.02/GB/month — your moments table will be tiny.
- **BigQuery `VECTOR_SEARCH` query**: charged as bytes scanned. With <100k
  moments this is negligible (under a cent per query).
- **Cloud Storage**: standard storage pricing for video files.
