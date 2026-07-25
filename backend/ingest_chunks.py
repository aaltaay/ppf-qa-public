import os
import json
import time
from dotenv import load_dotenv
import google.generativeai as genai
from pinecone import Pinecone

# Load .env from project root (or rely on exported env vars)
load_dotenv()

# 1. Configure Gemini
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    print("Error: GEMINI_API_KEY not set.")
    exit(1)
genai.configure(api_key=api_key)

# 2. Configure Pinecone
pc_key = os.environ.get("PINECONE_API_KEY")
if not pc_key:
    print("Error: PINECONE_API_KEY not set.")
    exit(1)
pc = Pinecone(api_key=pc_key)

INDEX_NAME = os.environ.get("PINECONE_INDEX", "course-qa-demo")
NAMESPACE = os.environ.get("PINECONE_NAMESPACE", "demo")
EMBED_TITLE = os.environ.get("EMBED_DOCUMENT_TITLE", "Course Q&A Demo")

# Ensure index exists
if INDEX_NAME not in [i.name for i in pc.list_indexes()]:
    print(f"Error: Pinecone index '{INDEX_NAME}' does not exist. Please create it first.")
    exit(1)

index = pc.Index(INDEX_NAME)

# 3. Load Chunks
CHUNKS_FILE = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "transcribe",
    "demo_chunks.json",
)
with open(CHUNKS_FILE, "r", encoding="utf-8") as f:
    chunks = json.load(f)

print(f"Loaded {len(chunks)} chunks from {CHUNKS_FILE}")

# 4. Ingest to Pinecone
batch_size = 50
vectors = []

print(f"Generating embeddings and upserting to index '{INDEX_NAME}', namespace '{NAMESPACE}'...")

for i, chunk in enumerate(chunks):
    text = chunk.get("text", "")
    if not text:
        continue

    max_retries = 3
    for attempt in range(max_retries):
        try:
            result = genai.embed_content(
                model="models/gemini-embedding-2",
                content=text,
                task_type="retrieval_document",
                title=EMBED_TITLE,
            )
            embedding = result["embedding"]

            vector_id = f"mod{chunk.get('module', 0)}-chunk-{i}"
            metadata = {
                "module": chunk.get("module", 0),
                "start_time": chunk.get("start_time", 0.0),
                "end_time": chunk.get("end_time", 0.0),
                "text": text,
            }

            vectors.append({
                "id": vector_id,
                "values": embedding,
                "metadata": metadata,
            })

            if len(vectors) >= batch_size or i == len(chunks) - 1:
                index.upsert(vectors=vectors, namespace=NAMESPACE)
                print(f"Upserted {len(vectors)} chunks into namespace '{NAMESPACE}'...")
                vectors = []
                time.sleep(0.5)

            break

        except Exception as e:
            if attempt < max_retries - 1:
                print(f"Error processing chunk {i} (attempt {attempt + 1}/{max_retries}): {e}")
                time.sleep(2)
            else:
                print(f"Error processing chunk {i} after {max_retries} attempts: {e}")

if vectors:
    index.upsert(vectors=vectors, namespace=NAMESPACE)
    print(f"Upserted final {len(vectors)} chunks into namespace '{NAMESPACE}'...")

print("Ingestion complete! Demo course knowledge base is now in Pinecone.")
