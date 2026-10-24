# TikTok research MCP

One tool, `search_videos(query, count=10)`, over the installed social-fetch client.

Stdio:

```bash
PYTHONPATH=. python -m research_mcp.server
```

Streamable HTTP:

```bash
PYTHONPATH=. MCP_TRANSPORT=streamable-http PORT=8765 python -m research_mcp.server
```

Endpoint: `http://127.0.0.1:8765/mcp`
