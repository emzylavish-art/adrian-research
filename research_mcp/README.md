# TikTok research MCP

`search_videos(query, count=10)` is unchanged. Universal tools are appended in `server.py` and described in the repository README.

Stdio:

```bash
PYTHONPATH=. python -m research_mcp.server
```

Streamable HTTP:

```bash
PYTHONPATH=. MCP_TRANSPORT=streamable-http PORT=8765 python -m research_mcp.server
```

Endpoint: `http://127.0.0.1:8765/mcp`
