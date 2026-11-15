# TikTok Research MCP

The original tool is still `search_videos`. It calls the installed `social-fetch` client with `source="tiktok"` and returns `url`, `video_id`, `title`, `description`, and `username`. It does not return view or like counts.

The appended layer adds universal tools. `get_post(url)` detects the platform and returns one normalized shape. Platform-named tools are not part of this layer. See [AUDIT.md](AUDIT.md) for what was actually proven.

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

`search_videos` is unchanged. The universal tools are registered on the same server. This repository is not wired into Adrian OS, Grokbot, or Google Sheets, and this branch does not deploy.

Do not deploy an untagged revision. This pull request does not create a release tag.

## Universal tools

`get_post`, `search_posts`, `get_profile`, `list_profile_posts`, `get_transcript`, `get_comments`, `get_comment_replies`, `get_trending`, `download_media`, `export_media`, `media_status`, `fetch_resource`, `search_hashtags`, `search_suggestions`, `search_shop_products`, `get_account_sample`.

Info tools return the keys in `research_mcp/util/schema.py`. Empty fields are null. Failures are in `errors` and do not crash the server. `get_trending`, `search_hashtags`, `search_suggestions`, and `search_shop_products` are TikTok-only and say so. They do not invent results for other platforms.

## Environment

| Variable | Default | Purpose |
| --- | --- | --- |
| `MCP_TRANSPORT` | `stdio` | `stdio` or `streamable-http` |
| `HOST` | `0.0.0.0` | HTTP bind address |
| `PORT` | `8765` | HTTP port |
| `SOCIAL_FETCH_DATA_DIR` | `./mcp-data` | local jobs and saved resources |
| `SOCIAL_FETCH_NS` | `research` | download namespace |
| `SOCIALFETCH_API_KEY` | unset | Social Fetch REST. Tools return an error dict when it is missing. |
| `EASYDOWN_API_KEY` | unset | EasyDown Bearer token. Same missing-key behavior. |
| `SOCIALFETCH_REGION` | unset | used by TikTok trending when `region` is omitted, otherwise `US` |

`8765` is only the default. If that port is taken, set `PORT` before starting HTTP mode.

EasyDown published costs, from its OpenAPI file: 1 credit for most platforms, 3 for YouTube, 2 for Threads, 2 for Kuaishou, 10 for Xiaohongshu. Failures are not charged. The response JSON does not report the charged amount.

Social Fetch tools copy `meta.creditsCharged` into `credits_charged`. They do not invent a price when that field is missing.

Vercel still invokes `app.py` with a 60 second limit. Use `download_media(..., wait=False)` there and poll `media_status`.

## Client config

```json
{
  "mcpServers": {
    "tiktok-research": {
      "command": "python",
      "args": ["-m", "research_mcp.server"],
      "env": {
        "PYTHONPATH": ".",
        "SOCIAL_FETCH_DATA_DIR": "./mcp-data"
      }
    }
  }
}
```

Put API keys in the environment. Do not commit them.
