import os
from dotenv import load_dotenv
from pinecone import Pinecone
import google.generativeai as genai

load_dotenv()

api_key = os.environ.get("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

PINECONE_INDEX = os.environ.get("PINECONE_INDEX", "course-qa-demo")
PINECONE_NAMESPACE = os.environ.get("PINECONE_NAMESPACE", "demo")


def load_chunks(filepath):
    """Stub kept for compatibility with older call sites."""
    return [], {}, None


def retrieve_chunks(query, current_module, top_n=5, threshold=0.0):
    """
    Embed the query via Gemini and search Pinecone under the configured namespace.
    """
    result = genai.embed_content(
        model="models/gemini-embedding-2",
        content=query,
        task_type="retrieval_query",
    )
    query_vector = result["embedding"]

    pc_key = os.environ.get("PINECONE_API_KEY")
    pc = Pinecone(api_key=pc_key)
    index = pc.Index(PINECONE_INDEX)

    filter_dict = {}
    if current_module:
        filter_dict = {"module": {"$eq": current_module}}

    search_response = index.query(
        namespace=PINECONE_NAMESPACE,
        vector=query_vector,
        top_k=top_n,
        include_metadata=True,
        filter=filter_dict if filter_dict else None,
    )

    retrieved_chunks = []
    for match in search_response["matches"]:
        if match["score"] > threshold:
            retrieved_chunks.append({
                "module": match["metadata"].get("module", 0),
                "start_time": match["metadata"].get("start_time", 0.0),
                "end_time": match["metadata"].get("end_time", 0.0),
                "text": match["metadata"].get("text", ""),
            })

    if current_module and not retrieved_chunks:
        fallback_response = index.query(
            namespace=PINECONE_NAMESPACE,
            vector=query_vector,
            top_k=top_n,
            include_metadata=True,
        )
        for match in fallback_response["matches"]:
            if match["score"] > threshold:
                retrieved_chunks.append({
                    "module": match["metadata"].get("module", 0),
                    "start_time": match["metadata"].get("start_time", 0.0),
                    "end_time": match["metadata"].get("end_time", 0.0),
                    "text": match["metadata"].get("text", ""),
                })

    return retrieved_chunks
