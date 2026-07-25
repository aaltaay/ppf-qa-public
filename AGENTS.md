# Course Q&A Demo — Agent Governance

> **Purpose:** RAG pipeline for a video-course Q&A widget (portfolio demo).  
> **Scope:** `backend/`, `transcribe/`, `frontend/`, `demo.html`

---

## Pipeline invariants

| # | Rule | Rationale |
|---|------|-----------|
| 1 | Answers MUST be grounded in retrieved transcript chunks only | Prevents hallucination on course content |
| 2 | System prompt MUST refuse off-topic questions | Keeps the assistant scoped to course material |
| 3 | Citations use `[Module X at MM:SS]` format | Frontend parses and renders seek links |
| 4 | Embeddings via `gemini-embedding-2` (3072-dim) | Must match Pinecone index dimension |
| 5 | Pinecone index/namespace from env vars | No hardcoded production identifiers |
| 6 | Secrets ONLY via `.env` / environment | Never commit API keys or local paths |
| 7 | Rate limit on `/ask` before LLM call | Cost + abuse protection |

## Environment contract

All backend scripts load config from `.env` (see `.env.example`):

```
GEMINI_API_KEY=
PINECONE_API_KEY=
PINECONE_INDEX=course-qa-demo
PINECONE_NAMESPACE=demo
```

Optional: `EMBED_DOCUMENT_TITLE` — passed to embedding API during ingest.

## Data flow

```
demo_chunks.json  →  ingest_chunks.py  →  Pinecone (namespace)
                                              ↓
User question  →  embed query  →  top-k retrieval  →  llm.py  →  answer + citations
```

### Chunk schema

```json
{
  "module": 1,
  "start_time": 0.0,
  "end_time": 28.5,
  "text": "Transcript excerpt..."
}
```

## Module boundaries

| Area | Owner path | Notes |
|------|------------|-------|
| API + RAG | `backend/` | FastAPI, retrieval, LLM, ingest |
| Transcription | `transcribe/` | Optional; demo uses `demo_chunks.json` |
| Widget UI | `frontend/` | Vanilla JS; adapters for video/lesson detection |
| Demo page | `demo.html` | Static HTML; not production LMS integration |

## Safe changes

- Add modules: extend `demo_chunks.json`, re-run ingest
- Tune retrieval: adjust `top_n`, `threshold` in `retrieval.py`
- Swap models: update model IDs in `llm.py` / `retrieval.py` (verify embedding dims)
- Theming: edit `frontend/widget.css` (IDs prefixed `course-qa-*` for scoping)

## Forbidden changes

- Hardcoding API keys or local secret file paths
- Hardcoding Pinecone index/namespace (use env vars)
- Removing citation format from system prompt
- Disabling rate limiting without replacement
- Committing `.env` or real credentials

## Verification checklist

Before publishing changes:

1. `rg -i "tesla|ppf|\.env\.secrets|C:\\Users|AIza|pcsk_|sk-"` → zero hits (except this doc's examples)
2. `.env.example` documents all required vars
3. `demo_chunks.json` contains only synthetic demo content
4. `python -m backend.main` starts; `/docs` shows **Course Q&A Demo API**

## Maintenance log

- **2026-07-24** — Public portfolio sanitization: removed proprietary course content, env-driven Pinecone config, demo corpus, governance doc.
