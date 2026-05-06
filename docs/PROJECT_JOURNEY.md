# Video Moments RAG — Project Journey

A step-by-step record of how this project was built from scratch.

---

## What We Built

A system that:
1. Takes a **video** as input
2. Uses **Gemini 2.5 Pro** to extract structured "moments" (scenes/beats) from the video
3. **Vectorizes** those moments using text embeddings
4. Stores them in **BigQuery** with vector search capability
5. Lets you **query** moments in natural language through an AI agent (RAG)

```
video ──► GCS ──► Gemini (segment-by-segment) ──► moments JSON
              ──► text-embedding-005 ──► BigQuery (VECTOR_SEARCH)
                                          ▲
                                          │
                              ADK agent (retrieve_moments,
                                         get_clip_url tools)
```

---

## Step 1: Project Planning

**Goal:** Build a video moment extraction + RAG query system using Google ADK and GCP.

**Decisions made:**
- Use **Google ADK** (Agent Development Kit) for the conversational agent
- Use **Gemini 2.5 Pro** on Vertex AI for multimodal video understanding
- Use **text-embedding-005** (768-dim) for vectorizing moment descriptions
- Start with a **Python CLI** (not a web app)
- Structure: `ingest` pipeline + `query` agent

**Reference:** Used an existing Quickplay metadata-enrichment notebook as inspiration for the Gemini video processing pattern.

---

## Step 2: Project Structure & Core Modules

Created the project at `D:\video_moments_rag\` with this layout:

```
video_moments_rag/
├── src/                    # Core application code
│   ├── config.py           # Central config from .env
│   ├── gcs_utils.py        # GCS upload, signed URLs
│   ├── video_segmenter.py  # Split long videos into chunks
│   ├── extractor.py        # Gemini calls with structured output
│   ├── embedder.py         # Text embedding (text-embedding-005)
│   ├── vector_store.py     # BigQuery VECTOR_SEARCH wrapper
│   ├── ingest.py           # End-to-end ingestion pipeline
│   └── agent/
│       ├── tools.py        # retrieve_moments, get_clip_url
│       └── agent.py        # ADK LlmAgent definition
├── scripts/                # CLI entry points
│   ├── ingest_video.py     # Ingest a video
│   ├── chat.py             # Chat with the agent
│   ├── setup_bq.py         # Create BigQuery table
│   └── smoke_test.py       # Staging connectivity test
├── prompts/moments/        # Gemini system instructions
├── schemas/moments.json    # Structured output schema
├── tests/                  # Unit tests (mocked, no GCP needed)
├── agents/                 # ADK discovery directory
├── .github/workflows/      # CI/CD pipelines
├── Dockerfile              # Container image
├── pyproject.toml          # Linting & test config
├── requirements.txt        # Production dependencies
└── requirements-dev.txt    # Dev dependencies (ruff, pytest)
```

### Key modules explained:

**`video_segmenter.py`** — Long videos are probed with `ffmpeg` and split into chunks of max 10 minutes. This is because Gemini works better with shorter segments.

**`extractor.py`** — Sends each video chunk to Gemini 2.5 Pro with a structured output schema. Gemini returns JSON with moments containing: title, description, timestamps, entities, actions, mood, keywords, etc. Segment-relative timestamps are offset back to absolute video time.

**`embedder.py`** — Converts each moment dict into a flat text string and embeds it using `text-embedding-005` (768 dimensions). This text representation is what makes semantic search possible.

**`vector_store.py`** — Stores moments + embeddings in BigQuery. Uses `VECTOR_SEARCH` with cosine distance for similarity queries. Supports filtering by video_id.

**`agent/tools.py`** — Two tools for the ADK agent:
- `retrieve_moments(query, top_k, video_id)` — embeds the query, searches BigQuery
- `get_clip_url(gcs_uri, start, end)` — generates a signed GCS URL for playback

**`agent/agent.py`** — An ADK `LlmAgent` that uses the two tools above to answer natural language questions about video moments.

---

## Step 3: GCP Setup

### Authentication
We needed **two separate auth flows** (this was a key learning):
- `gcloud auth application-default login` — for Python SDKs (ADC)
- `gcloud auth login` — for gcloud CLI commands

### GCP services enabled:
```bash
gcloud services enable aiplatform.googleapis.com storage.googleapis.com bigquery.googleapis.com
```

### Resources created:
- **GCS bucket:** `video-moments-rag-debraj-2026` (us-central1)
- **BigQuery dataset:** `moments`
- **BigQuery table:** `moments` (columns: moment_id, video_id, gcs_uri, moment_json, embedding)

### Configuration (`.env`):
```
GCP_PROJECT_ID=project-0a83db49-ed06-47c9-be5
GCP_LOCATION=us-central1
GCS_BUCKET=video-moments-rag-debraj-2026
GEMINI_MODEL=gemini-2.5-pro
EMBEDDING_MODEL=text-embedding-005
EMBEDDING_DIM=768
BQ_DATASET=moments
BQ_MOMENTS_TABLE=moments
```

---

## Step 4: The Vertex AI Vector Search Detour

**What happened:** We initially chose Vertex AI Vector Search for the vector database. Built `create_index.py` to create a streaming-update index and deploy it to an endpoint.

**Problems encountered:**
1. `algorithmConfig is required but missing` — the high-level SDK wasn't sending required metadata. Fixed by using the lower-level `aiplatform_v1` client with explicit protobuf structs.
2. `IndexEndpoint is not found` (404) — eventual consistency issue after creation. Fixed with idempotent lookups and retry logic.
3. **The deploy operation took 30+ minutes** and required a VM-backed endpoint.

**Why we stopped:** The user asked "why do we need a VM?" — Vertex AI Vector Search requires a deployed endpoint ($$$) even when idle. For a low-volume project, this is wasteful.

**Decision:** Switched to **BigQuery VECTOR_SEARCH** — serverless, pay-per-query, no idle cost. Queries take ~2 seconds instead of <100ms, but that's fine for this use case.

---

## Step 5: BigQuery Migration

Rewrote `vector_store.py` to use BigQuery instead of Vertex AI Vector Search:
- `ensure_table()` creates dataset + table (instant, no long-running operation)
- `upsert()` uses `load_table_from_json` for immediate queryability
- `query()` uses parameterized SQL with `VECTOR_SEARCH(..., distance_type => 'COSINE')`

The interface (method signatures) stayed identical, so `ingest.py` and `agent/tools.py` needed zero changes.

Created `scripts/cleanup_vector_search.py` to delete the abandoned Vertex AI resources.

---

## Step 6: Testing

Wrote **15 unit tests** across 4 test files, all using mocked GCP (no real API calls):

| File | Tests | What it covers |
|------|-------|---------------|
| `test_video_segmenter.py` | 6 | Video splitting edge cases (short, exact, long, overlap, tail) |
| `test_embedder.py` | 3 | Moment-to-text conversion (all fields, empty fields, missing keys) |
| `test_extractor.py` | 2 | Timestamp offsetting and multi-segment iteration |
| `test_agent_tools.py` | 4 | Query formatting, top_k clamping, video_id filtering, URL generation |

**Why mocked?** We test our logic, not Google's APIs. Mocked tests are fast, free, and run anywhere.

---

## Step 7: First Video Ingestion

Ingested a Big Bang Theory clip (29 seconds):

```bash
python scripts/ingest_video.py path/to/big_bang_theory.mp4
```

**Result:** Gemini extracted 3 moments with full coverage:
1. **Penny is Impressed by the Whiteboard** [00:00 - 00:07]
2. **Sheldon Dismisses Leonard's Work** [00:07 - 00:15]
3. **Leonard and Sheldon Argue About Physics** [00:15 - 00:29]

Each moment includes: title, description, scene_type, entities, actions, location, dialogue_summary, mood, keywords.

### Querying worked:
```
you> find funny moments in big_bang_theory
→ returned all 3 moments with timestamps

you> who is with the board?
→ "Leonard, Penny, and Sheldon are all near the whiteboard"
```

---

## Step 8: CI/CD Pipeline

Created 3 GitHub Actions workflows in branch `ci/github-actions-pipeline`:

### CI — Lint & Test (`ci.yml`)
**Triggers:** Every pull request and push to main
- **Lint job:** `ruff check` (lint rules) + `ruff format --check` (formatting)
- **Test job:** `pytest` with coverage + critical import verification

### CD — Build & Staging (`cd.yml`)
**Triggers:** Push to main (after merge)
- **Build job:** Docker image → Google Artifact Registry
- **Smoke test job:** Verifies BigQuery, GCS, and embedding model connectivity

### Deploy — Production (`deploy.yml`)
**Triggers:** Manual only (workflow_dispatch)
- Optional BigQuery table setup
- Deploy Docker image to Cloud Run
- Post-deploy smoke test
- Route traffic (production only)

### Supporting files:
- `Dockerfile` — Python 3.11-slim + ffmpeg
- `pyproject.toml` — ruff lint/format config + pytest settings
- `scripts/smoke_test.py` — staging connectivity checker
- `.dockerignore` — excludes .venv, tests, .git

### Code quality:
Applied `ruff` formatting to all 20+ source files — modernized type annotations (`dict` instead of `Dict`, `list` instead of `List`, `X | None` instead of `Optional[X]`).

**PR #1** merged with all CI checks passing (lint: 6s, tests: 56s).

---

## Step 9: GitHub Repository

Published to: **https://github.com/debrajaiwork-wq/video-moments-rag**

---

## Tech Stack Summary

| Component | Technology |
|-----------|-----------|
| Language | Python 3.11+ |
| AI Model | Gemini 2.5 Pro (Vertex AI) |
| Embeddings | text-embedding-005 (768-dim) |
| Vector Store | BigQuery VECTOR_SEARCH (cosine distance) |
| Object Storage | Google Cloud Storage |
| Agent Framework | Google ADK (LlmAgent) |
| Video Processing | ffmpeg (probing + segmentation) |
| CLI Framework | Typer + Rich |
| Linting | Ruff |
| Testing | Pytest (mocked) |
| CI/CD | GitHub Actions |
| Containerization | Docker |
| Deployment Target | Google Cloud Run |

---

## Costs

| Service | Cost |
|---------|------|
| Gemini 2.5 Pro | ~$0.005-0.02 per minute of video |
| text-embedding-005 | ~$0.0001 per 1k tokens (basically free) |
| BigQuery storage | ~$0.02/GB/month (tiny table) |
| BigQuery VECTOR_SEARCH | Under a cent per query (<100k moments) |
| Cloud Storage | Standard pricing for video files |
| **Vertex AI Vector Search** | **Avoided — would have cost $$$$/month for idle endpoint** |

---

## Key Learnings

1. **Two auth systems in GCP** — ADC (for Python SDKs) vs gcloud CLI auth are separate flows
2. **Vertex AI Vector Search is expensive** — requires a deployed endpoint with VMs. BigQuery VECTOR_SEARCH is serverless and much cheaper for low-volume use
3. **Structured output from Gemini** — using `response_schema` ensures consistent JSON without post-processing
4. **Segment offsetting** — when processing video in chunks, timestamps must be shifted back to absolute video time
5. **Mock testing** — test your logic, not the cloud provider's API. Keeps tests fast, free, and reliable
6. **CI/CD from day one** — catches formatting and logic issues before they reach production
