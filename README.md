# mcp-gemini-support-agent
## Background
Enterprise support teams handle large volumes of repetitive IT requests related to VPN access, authentication, software installation, and permissions. Relevant information is often scattered across knowledge bases, internal documentation, and historical support tickets, making it time-consuming for employees to find the right solution.

Standalone LLMs may produce hallucinated answers when they lack access to enterprise-specific knowledge. To improve reliability, this project builds an Enterprise AI Support Agent that combines RAG, function calling, and ticket workflow automation to deliver citation-grounded responses and automatically create ticket drafts for unresolved issues.
