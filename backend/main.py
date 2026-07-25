from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os

from backend.retrieval import retrieve_chunks
from backend.llm import get_answer
from backend.rate_limit import check_rate_limit

app = FastAPI(title="Course Q&A Demo API")

# Local demo origins only — no wildcard + credentials (invalid CORS combo)
_default_origins = "http://localhost:8001,http://127.0.0.1:8001,http://localhost:5500,http://127.0.0.1:5500"
CORS_ORIGINS = [
    origin.strip()
    for origin in os.environ.get("CORS_ORIGINS", _default_origins).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

class HistoryItem(BaseModel):
    role: str
    content: str

class AskRequest(BaseModel):
    question: str
    current_module: Optional[int] = None
    history: List[HistoryItem] = []

@app.post("/ask")
async def ask_question(req: AskRequest, request: Request):
    # IP-based Rate limiting
    client_ip = request.client.host if request.client else "127.0.0.1"
    if not check_rate_limit(client_ip):
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Try again later.")

    if not req.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    # 1. Retrieval (Pinecone Vector Search)
    try:
        top_chunks = retrieve_chunks(req.question, req.current_module)
    except Exception:
        raise HTTPException(status_code=500, detail="Database retrieval failed.")
        
    if not top_chunks:
        # Provide an empty context if nothing above threshold is found
        top_chunks = []
    
    # 2. LLM Call
    answer = get_answer(req.question, top_chunks, req.history)

    # 3. Return answer to frontend (Citations are embedded in text)
    return {
        "answer": answer,
        "citations_info": "Citations are embedded in the text."
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8001, reload=True)
