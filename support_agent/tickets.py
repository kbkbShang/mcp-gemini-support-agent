from __future__ import annotations

from datetime import datetime, timezone
import json
import re

from support_agent.config import TICKET_DRAFTS_FILE, TICKETS_FILE

TOKEN_PATTERN = re.compile(r"[a-zA-Z0-9_\-]{2,}")


def _tokenize(text: str) -> set[str]:
    return {t.lower() for t in TOKEN_PATTERN.findall(text)}


class TicketStore:
    def __init__(self) -> None:
        self._ensure_files()

    def _ensure_files(self) -> None:
        if not TICKETS_FILE.exists():
            TICKETS_FILE.parent.mkdir(parents=True, exist_ok=True)
            TICKETS_FILE.write_text("[]", encoding="utf-8")
        if not TICKET_DRAFTS_FILE.exists():
            TICKET_DRAFTS_FILE.parent.mkdir(parents=True, exist_ok=True)
            TICKET_DRAFTS_FILE.write_text("[]", encoding="utf-8")

    def _read_json(self, path):
        return json.loads(path.read_text(encoding="utf-8"))

    def _write_json(self, path, data):
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def search_tickets(self, query: str, top_k: int = 5) -> list[dict]:
        tickets = self._read_json(TICKETS_FILE)
        q = _tokenize(query)
        scored = []
        for ticket in tickets:
            text = f"{ticket.get('title', '')} {ticket.get('description', '')} {' '.join(ticket.get('tags', []))}"
            tks = _tokenize(text)
            overlap = len(q & tks)
            score = overlap / (len(q) + 1)
            if score > 0:
                scored.append((score, ticket))
        scored.sort(key=lambda x: x[0], reverse=True)
        out = []
        for score, t in scored[:top_k]:
            out.append(
                {
                    "ticket_id": t["ticket_id"],
                    "title": t["title"],
                    "status": t["status"],
                    "score": round(float(score), 4),
                    "resolution": t.get("resolution", ""),
                }
            )
        return out

    def create_ticket_draft(self, session_id: str, query: str, evidence: list[str]) -> dict:
        drafts = self._read_json(TICKET_DRAFTS_FILE)
        draft_id = f"draft-{len(drafts) + 1:04d}"
        draft = {
            "draft_id": draft_id,
            "session_id": session_id,
            "query": query,
            "evidence": evidence,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "status": "draft",
        }
        drafts.append(draft)
        self._write_json(TICKET_DRAFTS_FILE, drafts)
        return draft
