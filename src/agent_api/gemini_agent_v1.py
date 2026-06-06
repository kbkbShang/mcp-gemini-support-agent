import json
import os
from urllib import response
from dotenv import load_dotenv
from google import genai
from google.genai import types

from src.agent_api.tools_client import (
    call_search_kb,
    call_search_tickets,
    call_create_ticket_draft,
)


load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def search_kb(query: str, top_k: int = 3) -> dict:
    """Search internal knowledge base articles.

    Args:
        query: User support question.
        top_k: Number of knowledge base chunks to return.
    """
    return call_search_kb(query=query, top_k=top_k)


def search_tickets(query: str, status: str | None = "resolved", tags: list[str] | None = None, top_k: int = 3) -> dict:
    """Search historical support tickets.

    Args:
        query: User support question.
        status: Optional ticket status filter.
        tags: Optional ticket tags filter, such as vpn, sso, mfa, license, permission, etc.
        top_k: Number of tickets to return.
    """
    return call_search_tickets(query=query, status=status, tags=tags, top_k=top_k)


def create_ticket_draft(
    title: str,
    description: str,
    priority: str = "medium",
    tags: list[str] | None = None,
) -> dict:
    """Create a support ticket draft.

    Args:
        title: Draft ticket title.
        description: Draft ticket description.
        priority: Ticket priority: low, medium, high, or critical.
        tags: Ticket tags.
    """
    return call_create_ticket_draft(
        title=title,
        description=description,
        priority=priority,
        tags=tags or [],
    )


SYSTEM_INSTRUCTION = """
You are an enterprise IT support agent.

You must:
- Use tools to retrieve evidence before answering.
- Prefer search_kb for knowledge base evidence.
- Use search_tickets when historical cases may help.
- Do not invent unsupported answers.
- If there is not enough evidence, create a ticket draft.
- Return only valid JSON with this exact shape:

{
  "answer": "...",
  "citations": [
    {"doc_id": "...", "chunk_id": "...", "quote": "..."}
  ],
  "confidence": 0.0,
  "next_actions": ["..."],
  "ticket_draft": {"created": false, "draft_id": null}
}
"""


def run_gemini_agent(query: str) -> dict:
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=query,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                tools=[search_kb, search_tickets, create_ticket_draft],
            ),
        )

        print("===== GEMINI RAW RESPONSE =====")
        print(response)
        print("===== GEMINI TEXT =====")
        print(response.text)

        text = response.text or ""

        if not text.strip():
            return {
                "answer": "Gemini did not return a text response. It may have made a tool call but did not produce final JSON.",
                "citations": [],
                "confidence": 0.0,
                "next_actions": [],
                "ticket_draft": {"created": False, "draft_id": None},
            }

        return json.loads(text.strip())

    except Exception as e:
        return {
            "answer": f"Agent failed to generate a response: {str(e)}",
            "citations": [],
            "confidence": 0.0,
            "next_actions": ["Try again or create a support ticket manually."],
            "ticket_draft": {"created": False, "draft_id": None},
        }