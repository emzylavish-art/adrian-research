# TikTok Research MCP

Private research layer for public TikTok keyword search. One MCP tool: `search_videos`.

It calls the installed `social-fetch` client (`source="tiktok"`) and returns `url`, `video_id`, `title`, `description`, and `username`. It does not return view or like counts.

## Requirements

- Python 3.10+
- `mcp` 1.x (`mcp>=1.9,<2`)
- [social-fetch](https://github.com/Karnaf0katom/social-fetch) installed so `social_fetch` imports

```bash
pip install "mcp>=1.9,<2"
pip install "git+https://github.com/Karnaf0katom/social-fetch.git"
```

## Start (stdio)

From this repository:

```bash
PYTHONPATH=. python -m research_mcp.server
```

## Start (Streamable HTTP)

```bash
PYTHONPATH=. MCP_TRANSPORT=streamable-http PORT=8765 python -m research_mcp.server
```

Endpoint: `http://127.0.0.1:8765/mcp`

Optional data directory:

```bash
SOCIAL_FETCH_DATA_DIR=./mcp-data PYTHONPATH=. MCP_TRANSPORT=streamable-http PORT=8765 python -m research_mcp.server
```

## Status

Research layer is ready. It is not connected to Grokbot and it does not write to Google Sheets.
