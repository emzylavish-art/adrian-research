"""TikTok research MCP. Does not modify social-fetch.

Start with stdio (default):

    PYTHONPATH=. python -m research_mcp.server

Start with Streamable HTTP:

    PYTHONPATH=. MCP_TRANSPORT=streamable-http PORT=8765 python -m research_mcp.server

The HTTP endpoint is http://127.0.0.1:8765/mcp
"""
from __future__ import annotations

import os
import re

from mcp.server.fastmcp import FastMCP
from social_fetch.client import Client

mcp = FastMCP(
    "tiktok-research",
    host=os.getenv("HOST", "127.0.0.1"),
    port=int(os.getenv("PORT", "8765")),
)
_client = Client(
    data_dir=os.getenv("SOCIAL_FETCH_DATA_DIR", "/tmp/tiktok-research-working/mcp-data")
)
_VIDEO = re.compile(r"tiktok\.com/@([^/]+)/video/(\d+)")


@mcp.tool()
def search_videos(query: str, count: int = 10) -> list[dict]:
    """Search public TikTok videos by keyword using the indexed web results."""
    if not isinstance(query, str) or not query.strip():
        raise ValueError("query is required")
    count = max(1, min(int(count), 20))
    result = _client.search(query.strip(), source="tiktok", count=count)
    rows = []
    for item in result.get("results") or []:
        url = item.get("url") or ""
        match = _VIDEO.search(url)
        if not match:
            continue
        rows.append({
            "url": url,
            "video_id": match.group(2),
            "title": item.get("title") or "",
            "description": item.get("description") or "",
            "username": match.group(1),
        })
    return rows


def main() -> None:
    mcp.run(transport=os.getenv("MCP_TRANSPORT", "stdio"))


if __name__ == "__main__":
    main()
