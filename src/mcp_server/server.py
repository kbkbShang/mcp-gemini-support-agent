from fastapi import FastAPI

from src.rag.retriever import search_kb as rag_search_kb
from src.rag.retriever import get_kb_doc as rag_get_kb_doc

app = FastAPI(title="MCP Gemini Support Agent", description="API for MCP Gemini Support Agent", version="1.0.0")

## This is a mock implementation of the tool server. In a real implementation, this would connect to a knowledge base and ticketing system.
@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "tool_server",
        "kb_index_exists": False,
        "tickets_readable": False
    }
   
# Tool endpoint for searching the knowledge base. 
# Performs a similarity search in Chroma 
# and returns the top K most relevant chunks. 
# Each chunk includes doc_id, chunk_id, score, heading, and text.
@app.post("/tools/search_kb")
def search_kb(payload: dict):
    query = payload.get("query")
    top_k = payload.get("top_k", 5)

    if not query:
        return {
            "tool": "search_kb",
            "query": query,
            "top_k": top_k,
            "results": []
        }

    results = rag_search_kb(query=query, top_k=top_k)

    return {
        "tool": "search_kb",
        "query": query,
        "top_k": top_k,
        "results": results
    }

# Tool endpoint for retrieving a full KB document by doc_id.
# Returns the document content and metadata (e.g. source path).
@app.post("/tools/get_kb_doc")
def get_kb_doc(payload: dict):
    doc_id = payload.get("doc_id")

    if not doc_id:
        return {
            "tool": "get_kb_doc",
            "doc_id": doc_id,
            "content": None,
            "metadata": {},
            "error": "doc_id is required"
        }

    doc = rag_get_kb_doc(doc_id)

    if doc is None:
        return {
            "tool": "get_kb_doc",
            "doc_id": doc_id,
            "content": None,
            "metadata": {},
            "error": "document not found"
        }

    return {
        "tool": "get_kb_doc",
        **doc
    }

## This is a mock implementation. In a real implementation, this would search for relevant tickets in the ticketing system and return them.
@app.post("/tools/search_tickets")
def search_tickets(payload: dict):
    return {
        "tool": "search_tickets",
        "query": payload.get("query"),
        "results": []
    }

## This is a mock implementation. In a real implementation, this would create a draft ticket in the ticketing system and return the draft ID.
@app.post("/tools/create_ticket_draft")
def create_ticket_draft(payload: dict):
    return {
        "tool": "create_ticket_draft",
        "draft_id": "DRF-0001",
        "saved": False
    }
