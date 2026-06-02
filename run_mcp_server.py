import uvicorn

if __name__ == "__main__":
    uvicorn.run("support_agent.mcp_server:app", host="0.0.0.0", port=8001, reload=False)
