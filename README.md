# TikTok Research MCP

The original tool is still `search_videos`. It calls the installed `social-fetch` client with `source="tiktok"` and returns `url`, `video_id`, `title`, `description`, and `username`. It does not return view or like counts.

The appended layer adds universal tools. `get_post(url)` detects the platform and returns one normalized shape. Platform-named tools are not part of this layer. See [AUDIT.md](AUDIT.md) for what was actually proven.

## Install

Python 3.10+ and `mcp` 1.x (`mcp>=1.9,<2`). social-fetch is one line:

```bash
pip install "git+https://github.com/Karnaf0katom/social-fetch.git"
```

That URL installed in the audit. Do not replace it with a guessed package name.

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

`search_videos` is unchanged. The universal tools are registered on the same server. Adrian OS is unregistered and stays out. See [unregistered platforms](docs/unregistered-platforms.md).

Do not tag and do not deploy until the [release checklist](docs/RELEASE.md) has a green live search and a green live download. The manual smoke skips until `SOCIALFETCH_API_KEY` exists. A tag does not skip. This branch does not deploy.

## Universal tools

`get_post`, `search_posts`, `get_profile`, `list_profile_posts`, `get_transcript`, `get_comments`, `get_comment_replies`, `get_trending`, `download_media`, `export_media`, `media_status`, `fetch_resource`, `search_hashtags`, `search_suggestions`, `search_shop_products`, `get_account_sample`.

Info tools return the keys in `research_mcp/util/schema.py`. Empty fields are null. Failures are in `errors` and do not crash the server. `get_trending`, `search_hashtags`, `search_suggestions`, and `search_shop_products` are TikTok-only and say so. They do not invent results for other platforms.

The next TikTok tools are appended below that layer and do not replace `search_videos`. They are `search_tiktok_videos`, `search_tiktok_top`, `search_tiktok_users`, `list_tiktok_followers`, `list_tiktok_following`, `get_tiktok_region`, `get_tiktok_audience`, `get_tiktok_engagement`, `get_tiktok_live`, `get_tiktok_live_info`, `get_tiktok_hosted_media`, `list_tiktok_collection`, `get_tiktok_song`, `list_tiktok_sound_videos`, `list_tiktok_store_products`, `get_tiktok_product`, `list_tiktok_product_reviews`, `list_tiktok_showcase`, `get_tiktok_ad`, and `search_tiktok_ads`. Audience, engagement, and hosted media stay local until `confirm=True`. `credits_charged` still comes from the response.

## Environment

Required to start from this repository:

| Variable | Value |
| --- | --- |
| `PYTHONPATH` | `.` |

Required for the tools that call a paid API. Missing keys return an error dict and do not open a socket. The integration workflow stays skipped until the matching GitHub secret exists.

| Variable | Header | Used by |
| --- | --- | --- |
| `SOCIALFETCH_API_KEY` | `x-api-key` | Social Fetch REST, including TikTok and Bluesky |
| `EASYDOWN_API_KEY` | `Authorization: Bearer` | EasyDown `POST /api/v1/parse` and platform parse |

Optional process settings:

| Variable | Default | Purpose |
| --- | --- | --- |
| `MCP_TRANSPORT` | `stdio` | `stdio` or `streamable-http` |
| `HOST` | `0.0.0.0` | HTTP bind address |
| `PORT` | `8765` | HTTP port. Set this if 8765 is taken. |
| `SOCIAL_FETCH_DATA_DIR` | `./mcp-data` | local jobs, saved resources, and the release proof |
| `SOCIAL_FETCH_NS` | `research` | download namespace |
| `SOCIALFETCH_REGION` | `US` | TikTok trending region when the tool argument is omitted |
| `LIVE_SEARCH_QUERY` | `cat` | release-gate search only |
| `LIVE_DOWNLOAD_URL` | `https://www.youtube.com/watch?v=jNQXAC9IVRw` | release-gate download only |
| `LIVE_DOWNLOAD_TIMEOUT` | `900` | release-gate download timeout in seconds |

The installed library also reads `FOOTAGE_DOWNLOAD_ROOT`, `FOOTAGE_SEARCH_PROVIDER`, `BRAVE_SEARCH_API_KEY`, `BRAVE_API_KEY`, `SERPER_API_KEY`, `SOCIAL_FETCH_COBALT_URL`, and `XDG_DATA_HOME`. None of those are required. Leave them unset unless you already use them.

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
