from __future__ import annotations

from dataclasses import dataclass

from support_agent.kb import KBIndex
from support_agent.tickets import TicketStore


ESCALATION_TERMS = {"escalate", "无法", "人工", "still", "cannot", "can't", "error persists"}
MIN_CONFIDENCE = 0.2
MAX_CONFIDENCE = 0.95
DRAFT_CONFIDENCE_THRESHOLD = 0.45


@dataclass
class AgentResult:
    answer: str
    citations: list[dict]
    confidence: float
    next_actions: list[str]
    ticket_draft: dict | None


class SupportAgent:
    def __init__(self) -> None:
        self.kb = KBIndex()
        self.tickets = TicketStore()

    def run(self, query: str, session_id: str) -> AgentResult:
        kb_hits = self.kb.search(query, top_k=3)
        ticket_hits = self.tickets.search_tickets(query, top_k=2)

        top_score = kb_hits[0]["score"] if kb_hits else 0.0
        confidence = round(min(MAX_CONFIDENCE, max(MIN_CONFIDENCE, top_score)), 2)

        evidence = [f"{h['doc_id']}: {h['title']}" for h in kb_hits]
        if ticket_hits:
            evidence.append(f"related_ticket: {ticket_hits[0]['ticket_id']}")

        answer_lines = []
        if kb_hits:
            answer_lines.append("根据知识库检索结果，建议按以下顺序排查：")
            for i, hit in enumerate(kb_hits, start=1):
                answer_lines.append(f"{i}. {hit['title']}（匹配度 {hit['score']}）")
        else:
            answer_lines.append("当前知识库未检索到高相关文档，建议补充更多上下文信息。")

        if ticket_hits:
            answer_lines.append(f"历史工单 {ticket_hits[0]['ticket_id']} 可能相关：{ticket_hits[0]['resolution']}")

        next_actions = [
            "先执行知识库中的排查步骤并记录结果",
            "若问题持续，补充错误日志和复现步骤",
        ]

        needs_draft = confidence < DRAFT_CONFIDENCE_THRESHOLD or any(term in query.lower() for term in ESCALATION_TERMS)
        ticket_draft = None
        if needs_draft:
            ticket_draft = self.tickets.create_ticket_draft(session_id=session_id, query=query, evidence=evidence)
            next_actions.append("已生成 ticket draft，请客服或工程团队确认后提交")

        citations = [
            {
                "source": "kb",
                "id": h["doc_id"],
                "title": h["title"],
                "path": h["path"],
                "score": h["score"],
            }
            for h in kb_hits
        ]
        citations.extend(
            {
                "source": "ticket",
                "id": t["ticket_id"],
                "title": t["title"],
                "score": t["score"],
            }
            for t in ticket_hits
        )

        return AgentResult(
            answer="\n".join(answer_lines),
            citations=citations,
            confidence=confidence,
            next_actions=next_actions,
            ticket_draft=ticket_draft,
        )
