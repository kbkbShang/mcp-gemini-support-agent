import unittest

from fastapi.testclient import TestClient

from support_agent.api import app as agent_app
from support_agent.mcp_server import app as mcp_app


class AgentApiTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(agent_app)

    def test_chat_returns_required_fields(self):
        res = self.client.post(
            "/chat",
            json={"query": "API 返回 429 如何解决", "session_id": "test-session-1"},
        )
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertIn("answer", body)
        self.assertIn("citations", body)
        self.assertIn("confidence", body)
        self.assertIn("next_actions", body)
        self.assertIn("ticket_draft", body)
        self.assertGreater(len(body["citations"]), 0)


class MCPServerTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(mcp_app)

    def test_search_kb_tool(self):
        res = self.client.post(
            "/call",
            json={"tool_name": "search_kb", "arguments": {"query": "password reset", "top_k": 2}},
        )
        self.assertEqual(res.status_code, 200)
        items = res.json()["result"]
        self.assertTrue(items)
        self.assertIn("doc_id", items[0])

    def test_create_ticket_draft_tool(self):
        res = self.client.post(
            "/call",
            json={
                "tool_name": "create_ticket_draft",
                "arguments": {
                    "session_id": "test-session-2",
                    "query": "still cannot resolve issue",
                    "evidence": ["kb-001"],
                },
            },
        )
        self.assertEqual(res.status_code, 200)
        draft = res.json()["result"]
        self.assertEqual(draft["status"], "draft")


if __name__ == "__main__":
    unittest.main()
