# mcp-gemini-support-agent

一个可交付的企业支持 Agent Demo：**用户提问 → Agent 调用工具 → KB / ticket 检索 → 基于证据回答 + citations → 必要时创建 ticket draft → 离线评测输出**。

## 架构图

```text
User Query
   |
   v
FastAPI Agent API (/chat)
   |----> KB Retriever (FAISS index over markdown docs)
   |----> Ticket Search (mock historical tickets)
   |----> Draft Writer (ticket_drafts.json)
   v
Answer + citations + confidence + next_actions + ticket_draft

MCP-style Tool Server
  - /tools (discover tools)
  - /call  (search_kb/get_kb_doc/search_tickets/create_ticket_draft)
  - /health
```

## 项目内容

- `support_agent/api.py`: Agent API (`POST /chat`)
- `support_agent/mcp_server.py`: MCP-style tool server
- `data/kb/*.md`: 11 篇 KB 文档（10-15 要求内）
- `data/tickets/history.json`: 60 条历史工单（50-80 要求内）
- `data/tickets/ticket_drafts.json`: 无法解决时写入 ticket draft
- `eval/questions.json`: 20 条测试问题
- `eval/run_eval.py`: 生成 `eval/report.json`

## 启动命令

```bash
pip install -r requirements.txt
python run_agent_api.py      # http://localhost:8000
python run_mcp_server.py     # http://localhost:8001
```

## Demo curl

```bash
curl -s http://localhost:8000/chat \
  -H 'Content-Type: application/json' \
  -d '{"query":"API 返回 429 怎么办？","session_id":"demo-001"}' | jq

curl -s http://localhost:8001/call \
  -H 'Content-Type: application/json' \
  -d '{"tool_name":"search_kb","arguments":{"query":"password reset","top_k":3}}' | jq
```

## Sample Response (/chat)

```json
{
  "answer": "根据知识库检索结果，建议按以下顺序排查：...",
  "citations": [
    {"source":"kb","id":"kb-004","title":"API Rate Limit Exceeded","path":"data/kb/api-rate-limit.md","score":0.31}
  ],
  "confidence": 0.31,
  "next_actions": [
    "先执行知识库中的排查步骤并记录结果",
    "若问题持续，补充错误日志和复现步骤"
  ],
  "ticket_draft": null
}
```

## 运行评测

```bash
python eval/run_eval.py
cat eval/report.json
```

本仓库已包含 `eval/report.json`（由脚本生成）。

## Future Improvements

1. 使用真实向量模型（如 bge/e5）替换 hash embedding。
2. 接入真实工单系统（Jira/ServiceNow）和状态回写。
3. 增加多轮会话记忆、工具调用规划与 guardrails。
4. 增加在线 A/B 与人工质检闭环。
