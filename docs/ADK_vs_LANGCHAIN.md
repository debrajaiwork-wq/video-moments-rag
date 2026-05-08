# Google ADK vs LangChain — Side-by-Side Comparison

Both branches implement the same Video Moments RAG system with identical functionality.
The only difference is the agent/embedding framework.

- **main** branch → Google ADK
- **feat/langchain** branch → LangChain

---

## Files Changed

| File | Google ADK (main) | LangChain (feat/langchain) | Changed? |
|------|-------------------|---------------------------|----------|
| `src/embedder.py` | `google.genai.Client` | `VertexAIEmbeddings` | Yes |
| `src/extractor.py` | `google.genai.Client` | `google.genai.Client` (kept) | Minimal |
| `src/vector_store.py` | Custom BigQuery wrapper | Custom BigQuery wrapper | No |
| `src/agent/tools.py` | Plain functions | `@tool` decorated functions | Yes |
| `src/agent/agent.py` | `LlmAgent` | `create_tool_calling_agent` + `AgentExecutor` | Yes |
| `scripts/chat.py` | Async `InMemoryRunner` | Sync `AgentExecutor.invoke` | Yes |
| `src/config.py` | Same | Same | No |
| `src/gcs_utils.py` | Same | Same | No |
| `src/video_segmenter.py` | Same | Same | No |
| `src/ingest.py` | Same | Same | No |

**6 files unchanged, 4 files rewritten, 1 kept with minor edits.**

---

## Code Comparison

### Agent Definition

```python
# ─── Google ADK ───
from google.adk.agents import LlmAgent

agent = LlmAgent(
    name="video_moments_agent",
    model="gemini-2.5-pro",
    instruction=INSTRUCTIONS,
    tools=[retrieve_moments, get_clip_url],
)

# ─── LangChain ───
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_google_vertexai import ChatVertexAI

llm = ChatVertexAI(model_name="gemini-2.5-pro")
prompt = ChatPromptTemplate.from_messages([...])
agent = create_tool_calling_agent(llm, tools, prompt)
executor = AgentExecutor(agent=agent, tools=tools)
```

**ADK: 6 lines → LangChain: 8 lines.** ADK is more concise. LangChain requires explicit prompt template and executor setup.

### Tool Definition

```python
# ─── Google ADK ───
def retrieve_moments(query: str, top_k: int = 5) -> dict:
    """Search moments."""
    ...

# ─── LangChain ───
@tool
def retrieve_moments(query: str, top_k: int = 5) -> dict:
    """Search moments."""
    ...
```

**Nearly identical.** LangChain just adds a `@tool` decorator. The docstring becomes the tool description.

### Embeddings

```python
# ─── Google ADK ───
from google import genai
client = genai.Client(vertexai=True, project=..., location=...)
result = client.models.embed_content(
    model="text-embedding-005",
    contents=texts,
    config=types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT"),
)
vectors = [e.values for e in result.embeddings]

# ─── LangChain ───
from langchain_google_vertexai import VertexAIEmbeddings
model = VertexAIEmbeddings(model_name="text-embedding-005")
vectors = model.embed_documents(texts)
```

**LangChain is simpler.** One class, one method call. ADK requires manual config objects.

### Chat Loop

```python
# ─── Google ADK ───
runner = InMemoryRunner(agent=agent, app_name="video_moments_rag")
session = await runner.session_service.create_session(...)
async for event in runner.run_async(session_id=..., new_message=message):
    if event.content and event.content.parts:
        for part in event.content.parts:
            if part.text:
                chunks.append(part.text)

# ─── LangChain ───
executor = build_agent()
result = executor.invoke({"input": user_query, "chat_history": history})
reply = result["output"]
```

**LangChain is much simpler.** One line to get a response. ADK requires async iteration over events and manual text extraction from parts.

---

## Architecture Comparison

| Aspect | Google ADK | LangChain |
|--------|-----------|-----------|
| **Agent creation** | `LlmAgent(model, tools, instruction)` | `create_tool_calling_agent(llm, tools, prompt)` + `AgentExecutor` |
| **Tool definition** | Plain function with docstring | `@tool` decorator with docstring |
| **Embeddings** | `genai.Client.models.embed_content()` | `VertexAIEmbeddings.embed_documents()` |
| **Chat interface** | Async `InMemoryRunner` with event stream | Sync `AgentExecutor.invoke()` |
| **Conversation memory** | Built-in session management | Manual `chat_history` list |
| **Prompt template** | String passed as `instruction` | `ChatPromptTemplate` with placeholders |

---

## Dependencies

| Package | Google ADK | LangChain |
|---------|-----------|-----------|
| `google-adk` | Yes | No |
| `google-genai` | Yes | Yes (for extractor only) |
| `langchain` | No | Yes |
| `langchain-core` | No | Yes |
| `langchain-google-vertexai` | No | Yes |
| `langchain-google-community` | No | Yes |
| `google-cloud-bigquery` | Yes | Yes |
| `google-cloud-storage` | Yes | Yes |

**ADK: 2 framework packages → LangChain: 4 framework packages.** LangChain has more dependencies.

---

## Pros and Cons

### Google ADK

| Pros | Cons |
|------|------|
| Simpler API, less boilerplate | Gemini/Vertex AI only — no LLM portability |
| Built-in session management | Smaller community, fewer tutorials |
| Tight GCP integration | Less mature ecosystem |
| Fewer dependencies | Limited to Google's tooling |
| Works with `adk web` / `adk run` out of the box | Async-only chat interface |

### LangChain

| Pros | Cons |
|------|------|
| Swap LLMs in one line (OpenAI, Claude, Llama) | More abstraction layers |
| Huge ecosystem (700+ integrations) | More dependencies |
| Most recognized framework in job postings | Steeper learning curve |
| Built-in vector store integrations | Can feel over-engineered for simple tasks |
| Sync and async support | Rapid version changes can break code |
| Rich conversation memory options | |

---

## What Stayed the Same

These components are **framework-independent** — they work identically in both versions:

1. **Video segmentation** — ffmpeg probing and chunk splitting
2. **GCS utilities** — upload, signed URLs, JSON writes
3. **BigQuery vector store** — custom VECTOR_SEARCH wrapper
4. **Moment extraction** — Gemini structured output (kept google.genai in both)
5. **Ingestion pipeline** — orchestration logic
6. **CI/CD** — GitHub Actions workflows
7. **Tests** — 15/15 passing in both versions
8. **Docker** — same Dockerfile

**Key insight:** The agent framework only touches the "last mile" — how you wrap tools and talk to the user. The core pipeline (ingest, embed, store, search) is framework-agnostic.

---

## When to Choose Which

| Scenario | Recommendation |
|----------|---------------|
| All-in on GCP, small team | **Google ADK** — simpler, native |
| Need LLM portability | **LangChain** — swap models easily |
| Job interviews / portfolio | **LangChain** — more recognized |
| Production GCP deployment | **Google ADK** — tighter integration |
| Rapid prototyping | **LangChain** — more pre-built components |
| Learning agent concepts | **Google ADK** — less abstraction to understand |

---

## Test Results

Both versions: **15/15 tests passing**, lint clean, same CI pipeline.

| Test File | ADK | LangChain |
|-----------|-----|-----------|
| test_agent_tools.py (4) | Pass | Pass |
| test_embedder.py (3) | Pass | Pass |
| test_extractor.py (2) | Pass | Pass |
| test_video_segmenter.py (6) | Pass | Pass |
