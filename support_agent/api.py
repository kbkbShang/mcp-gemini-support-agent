from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel, Field

from support_agent.agent import SupportAgent

app = FastAPI(title="Support Agent API", version="0.1.0")
agent = SupportAgent()


class ChatRequest(BaseModel):
    query: str = Field(min_length=1)
    session_id: str = Field(min_length=1)


class ChatResponse(BaseModel):
    answer: str
    citations: list[dict]
    confidence: float
    next_actions: list[str]
    ticket_draft: dict | None


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest) -> ChatResponse:
    result = agent.run(query=payload.query, session_id=payload.session_id)
    return ChatResponse(
        answer=result.answer,
        citations=result.citations,
        confidence=result.confidence,
        next_actions=result.next_actions,
        ticket_draft=result.ticket_draft,
    )
