from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from support_agent.kb import KBIndex
from support_agent.tickets import TicketStore

app = FastAPI(title="MCP-style Tool Server", version="0.1.0")
kb = KBIndex()
tickets = TicketStore()


class ToolCall(BaseModel):
    tool_name: str
    arguments: dict


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/tools")
def list_tools() -> list[dict]:
    return [
        {"name": "search_kb", "arguments": ["query", "top_k"]},
        {"name": "get_kb_doc", "arguments": ["doc_id"]},
        {"name": "search_tickets", "arguments": ["query", "top_k"]},
        {"name": "create_ticket_draft", "arguments": ["session_id", "query", "evidence"]},
    ]


@app.post("/call")
def call_tool(payload: ToolCall) -> dict:
    args = payload.arguments
    if payload.tool_name == "search_kb":
        return {"result": kb.search(query=args.get("query", ""), top_k=int(args.get("top_k", 3)))}
    if payload.tool_name == "get_kb_doc":
        doc = kb.get_doc(args.get("doc_id", ""))
        if not doc:
            raise HTTPException(status_code=404, detail="doc not found")
        return {"result": doc}
    if payload.tool_name == "search_tickets":
        return {"result": tickets.search_tickets(query=args.get("query", ""), top_k=int(args.get("top_k", 5)))}
    if payload.tool_name == "create_ticket_draft":
        return {
            "result": tickets.create_ticket_draft(
                session_id=args.get("session_id", "unknown"),
                query=args.get("query", ""),
                evidence=args.get("evidence", []),
            )
        }
    raise HTTPException(status_code=400, detail=f"unknown tool: {payload.tool_name}")
