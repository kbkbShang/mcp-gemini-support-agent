import json
import os
from urllib import response
from dotenv import load_dotenv
from google import genai
from google.genai import types

from src.agent_api.tools_client import (
    call_search_kb,
    call_get_kb_doc,
    call_search_tickets,
    call_create_ticket_draft,
)

from pydantic import ValidationError
from src.agent_api.response_schemas import AgentResponse


load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def search_kb(query: str, top_k: int = 3) -> dict:
    """Search internal knowledge base articles.

    Args:
        query: User support question.
        top_k: Number of knowledge base chunks to return.
    """
    return call_search_kb(query=query, top_k=top_k)


def get_kb_doc(doc_id: str) -> dict:
    """Retrieve the full KB document.

    Args:
        doc_id: Document ID returned by search_kb.
    """
    return call_get_kb_doc(doc_id)


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

def extract_json_text(text: str) -> str:
    text = text.strip()

    if "```json" in text:
        start = text.find("```json") + len("```json")
        end = text.find("```", start)
        if end != -1:
            return text[start:end].strip()

    if "```" in text:
        start = text.find("```") + len("```")
        end = text.find("```", start)
        if end != -1:
            return text[start:end].strip()

    start = text.find("{")
    end = text.rfind("}")

    if start != -1 and end != -1 and end > start:
        return text[start:end + 1].strip()

    return text

def clean_json_text(text: str) -> str:
    text = text.strip()

    if text.startswith("```json"):
        text = text[len("```json"):].strip()

    if text.startswith("```"):
        text = text[len("```"):].strip()

    if text.endswith("```"):
        text = text[:-3].strip()

    return text

SYSTEM_INSTRUCTION = """
You are an enterprise IT support agent.

You must:

- Use search_kb first to retrieve relevant knowledge base evidence.
- If the retrieved chunks do not provide enough context, use get_kb_doc to retrieve the full document.
- Use search_tickets when similar historical support cases may be helpful.
- Prefer answering from retrieved evidence only.
- When citing evidence, use only information returned by the tools.
- Use get_kb_doc only to obtain additional context for answer generation.
- Even when get_kb_doc is used, citations must come from search_kb results.
- Citations must include the original doc_id, chunk_id, and quote from retrieved search_kb chunks.
- Do not include a "Citations" section inside the answer.
- Put citations only in the top-level citations array.
- Do not create new citations from the full document content.
- Do not output citations with an empty chunk_id.
- Do not invent facts, procedures, or unsupported solutions.
- If there is not enough evidence to answer confidently, create a ticket draft.
- You must never claim a ticket draft was created unless you actually called create_ticket_draft.
- If ticket_draft.created is true, the draft_id must come from the create_ticket_draft tool response.
- Never invent draft_id values.
- If create_ticket_draft was not called, ticket_draft.created must be false and draft_id must be null.
- For unresolved issues where a ticket draft is created, set confidence to 0.0 because no knowledge-base evidence was found.
- Keep answers concise, actionable, and grounded in retrieved evidence.

Return only valid JSON with this exact shape:

{
  "answer": "...",
  "citations": [
    {
      "doc_id": "...",
      "chunk_id": "...",
      "quote": "..."
    }
  ],
  "confidence": 0.0,
  "next_actions": [
    "..."
  ],
  "ticket_draft": {
    "created": false,
    "draft_id": null
  }
}
"""

def extract_tool_calls(response) -> list[str]:
    tool_calls = []

    history = getattr(response, "automatic_function_calling_history", []) or []

    for item in history:
        parts = getattr(item, "parts", []) or []

        for part in parts:
            function_call = getattr(part, "function_call", None)

            if function_call:
                tool_calls.append(function_call.name)

    return tool_calls

def run_gemini_agent(query: str) -> dict:
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=query,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                tools=[search_kb, get_kb_doc, search_tickets, create_ticket_draft],
            ),
        )

        tool_calls = extract_tool_calls(response)

        text = response.text or ""

        if not text.strip():
            return {
                "answer": "Gemini did not return a text response. It may have made a tool call but did not produce final JSON.",
                "citations": [],
                "confidence": 0.0,
                "next_actions": [],
                "ticket_draft": {
                    "created": False,
                    "draft_id": None,
                },
            }

        try:
            # First try parsing the full text directly.
            # This works when Gemini returns pure JSON.
            try:
                parsed_json = json.loads(text.strip())

            # If Gemini wraps JSON in markdown or extra text, extract JSON.
            except json.JSONDecodeError:
                json_text = extract_json_text(text)
                parsed_json = json.loads(json_text)

            validated_response = AgentResponse.model_validate(parsed_json)

            result = validated_response.model_dump()
            result["tool_calls"] = extract_tool_calls(response)

            return result

        except (json.JSONDecodeError, ValidationError) as e:
            return {
                "answer": text,
                "citations": [],
                "confidence": 0.0,
                "next_actions": [
                    f"Response parsing or validation failed: {str(e)}"
                ],
                "ticket_draft": {
                    "created": False,
                    "draft_id": None,
                },
            }

    except Exception as e:
        return {
            "answer": f"Agent failed to generate a response: {str(e)}",
            "citations": [],
            "confidence": 0.0,
            "next_actions": [
                "Try again or create a support ticket manually."
            ],
            "ticket_draft": {
                "created": False,
                "draft_id": None,
            },
        }