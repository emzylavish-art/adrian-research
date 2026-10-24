"""Vercel ASGI entry. Streamable HTTP MCP is served at /mcp."""
from research_mcp.server import mcp

app = mcp.streamable_http_app()
