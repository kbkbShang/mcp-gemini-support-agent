# MCP Gemini Support Agent

## Background

Enterprise support teams handle large volumes of repetitive IT requests related to VPN access, authentication, software installation, and permissions. Relevant information is often scattered across knowledge bases, internal documentation, and historical support tickets, making it time-consuming for employees to find the right solution.

Standalone LLMs may produce hallucinated answers when they lack access to enterprise-specific knowledge. To improve reliability, this project builds an Enterprise AI Support Agent that combines RAG, function calling, and ticket workflow automation to deliver citation-grounded responses and automatically create ticket drafts for unresolved issues.

---

## Project Goal

The goal of this project is to build a production-style AI support system that can:

- Retrieve relevant information from an internal knowledge base
- Search historical support tickets
- Generate citation-grounded responses
- Create ticket drafts for unresolved issues
- Evaluate system performance through offline testing

The project demonstrates how LLM agents can be integrated with enterprise workflows while maintaining reliability, traceability, and scalability.

---

## MVP Architecture

```text
User
  |
  v
FastAPI Agent API
  |
  v
Gemini Function Calling
  |
  v
MCP-style Tool Server
  |
  +--> search_kb()
  +--> get_kb_doc()
  +--> search_tickets()
  +--> create_ticket_draft()
  |
  v
Knowledge Base / Tickets
  |
  v
Citation-Grounded Response