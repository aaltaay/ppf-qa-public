# Course Q&A Demo

> [!CAUTION]
> This repository is a living snapshot of software under ongoing development. The public source code is updated as the work evolves and matures.
>
> It may contain incomplete features, known limitations, bugs, or security vulnerabilities. Do not deploy this snapshot to production or use it with real user data, payments, credentials, or other sensitive information without an independent security review.

A retrieval-augmented Q&A widget for video courses. Learners ask questions in a floating chat panel; answers are grounded in transcript chunks with clickable module/timestamp citations.

## Architecture

```
Video course page (demo.html + widget)
        │
        ▼ POST /ask
FastAPI backend (main.py)
        ├── retrieval.py  → Pinecone vector search (Gemini embeddings)
        └── llm.py        → Gemini 2.5 Flash answer generation
```

**Stack:** Python · FastAPI · Pinecone · Google Gemini (embeddings + generation) · vanilla JS widget

## Quick start

### 1. Install dependencies

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

### 2. Configure environment

```bash
copy .env.example .env
# Fill in GEMINI_API_KEY and PINECONE_API_KEY
```

| Variable | Description | Default |
|----------|-------------|---------|
| `GEMINI_API_KEY` | Google AI Studio key | — |
| `PINECONE_API_KEY` | Pinecone API key | — |
| `PINECONE_INDEX` | Pinecone index name | `course-qa-demo` |
| `PINECONE_NAMESPACE` | Pinecone namespace | `demo` |

Create a Pinecone index with **3072 dimensions** (compatible with `gemini-embedding-2`).

### 3. Ingest demo corpus

A sample transcript corpus ships at `transcribe/demo_chunks.json` (3 modules, 6 chunks):

```bash
python -m backend.ingest_chunks
```

### 4. Run the API

```bash
python -m backend.main
```

API docs: http://localhost:8001/docs

### 5. Open the demo page

Serve the repo root (any static file server) and open `demo.html`. The widget calls `http://localhost:8001/ask`.

## Project layout

```
backend/
  main.py           FastAPI app + /ask endpoint
  retrieval.py      Pinecone vector search
  llm.py            Answer generation with strict system prompt
  ingest_chunks.py  Embed + upsert transcript chunks
  rate_limit.py     IP-based rate limiting (10/hr, 50/day)
frontend/
  widget.js         Floating Q&A panel
  widget.css        Scoped widget styles
  adapters/         Video seek + lesson detection hooks
transcribe/
  demo_chunks.json  Sample transcript corpus (public demo)
  run_whisper.py    Single-video transcription via Gemini
  batch_transcribe.py
  chunk_transcripts.py
demo.html           Local demo page
```

## Transcription pipeline (optional)

Video files are not bundled with this repo — this public export ships a small transcript-only sample corpus (`transcribe/demo_chunks.json`) so the Q&A widget works out of the box. To build your own corpus from MP4 files:

1. Place videos in `modules/module N.mp4`
2. Run `python transcribe/batch_transcribe.py` — writes `transcribe/chunks.json`
3. Copy the output for ingest: `copy transcribe\chunks.json transcribe\demo_chunks.json` (Windows) or `cp transcribe/chunks.json transcribe/demo_chunks.json` (Unix)
4. Re-ingest: `python -m backend.ingest_chunks` (reads `transcribe/demo_chunks.json` by default)

`run_whisper.py` uses the **Gemini multimodal API** (not OpenAI Whisper) despite the filename — it is invoked by `batch_transcribe.py` per module.

## Rate limiting

The `/ask` endpoint enforces per-IP limits (10 requests/hour, 50/day) via in-memory tracking. For production, swap `rate_limit.py` for Redis or a gateway limiter.

## License

MIT — see [LICENSE](./LICENSE). This repository is a sanitized public extract from a private working monorepo, published for portfolio and demonstration purposes. Client names, credentials, and proprietary content have been replaced with placeholders or demo fixtures.
