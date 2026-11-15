"""TikTok research MCP.

Local stdio:

    PYTHONPATH=. python -m research_mcp.server

Local Streamable HTTP:

    PYTHONPATH=. MCP_TRANSPORT=streamable-http PORT=8765 python -m research_mcp.server

The local HTTP endpoint is http://127.0.0.1:8765/mcp
"""
from __future__ import annotations

import os
import re

from mcp.server.fastmcp import FastMCP
from social_fetch.web_search import FootageSearch

mcp = FastMCP(
    "tiktok-research",
    host=os.getenv("HOST", "0.0.0.0"),
    port=int(os.getenv("PORT", "8765")),
    stateless_http=True,
    json_response=True,
)
_search = FootageSearch.from_env(include_catalogs=False)
_VIDEO = re.compile(r"tiktok\.com/@([^/]+)/video/(\d+)")


@mcp.tool()
def search_videos(query: str, count: int = 10) -> list[dict]:
    """Search public TikTok videos by keyword using the indexed web results."""
    if not isinstance(query, str) or not query.strip():
        raise ValueError("query is required")
    count = max(1, min(int(count), 20))
    result = _search.search(query.strip(), source="tiktok", count=count)
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


# Appended universal social layer.
# Existing search_videos, the _VIDEO regex, FootageSearch.from_env, the
# FastMCP constructor, and main() stay exactly as they were. This block sits
# before the unchanged `if __name__` guard so registration runs before
# mcp.run() when the module is executed as a script. That placement is the
# smallest edit that makes appended tools visible to stdio and HTTP.
from research_mcp.util import service as _service


@mcp.tool()
def get_post(
    url: str,
    include_transcript: bool = False,
    include_comments: bool = False,
    download_media: bool = False,
) -> dict:
    """Look up one public post from any supported platform. Returns the same shape every time. Read errors before treating empty fields as real data. download_media writes a local job under the data directory and can take several minutes."""
    return _service.get_post(url, include_transcript, include_comments, download_media)


@mcp.tool()
def search_posts(query: str, platform: str | None = None, count: int = 10) -> list:
    """Search indexed public posts. platform restricts the search. When omitted, every social-fetch source is queried and the merged list is capped at 20. This does not change search_videos."""
    return _service.search_posts(query, platform, count, search=_search)


@mcp.tool()
def get_profile(handle: str, platform: str) -> dict:
    """Get a public profile card. TikTok and Bluesky use Social Fetch REST when SOCIALFETCH_API_KEY is set. Other library platforms return a bounded account sample, not a full profile."""
    return _service.get_profile(handle, platform)


@mcp.tool()
def list_profile_posts(handle: str, platform: str, count: int = 20, cursor: str | None = None) -> dict:
    """List posts for a profile. TikTok and Bluesky are paginated through Social Fetch. Other platforms return an explicit unsupported error instead of a fake page."""
    return _service.list_profile_posts(handle, platform, count, cursor)


@mcp.tool()
def get_transcript(url: str, use_ai_fallback: bool = False, language: str | None = None) -> dict:
    """Get a transcript. TikTok only. credits_charged is copied from the response when Social Fetch returns it. It is not a hardcoded price. Timing cues are stripped into transcript.text. Read errors before embedding."""
    return _service.get_transcript(url, use_ai_fallback, language)


@mcp.tool()
def get_comments(url: str, count: int = 20, cursor: str | None = None) -> dict:
    """Get public comments. TikTok uses its comments route. Bluesky returns replies included on the post lookup. Instagram and Reddit use the local library. Other platforms return an empty list plus an error entry."""
    return _service.get_comments(url, count, cursor)


@mcp.tool()
def get_comment_replies(comment_id: str, count: int = 20, cursor: str | None = None, url: str | None = None) -> dict:
    """Get replies to one comment. TikTok requires the parent comment id and the video url. Other platforms return an error entry, not a crash."""
    return _service.get_comment_replies(comment_id, count, cursor, url)


@mcp.tool()
def get_trending(platform: str | None = None, region: str | None = None, count: int = 20) -> dict:
    """Get a trending batch. This tool is honestly TikTok-only. Pass platform='tiktok'. Other values return unsupported_platform and do not call the network."""
    return _service.get_trending(platform, region, count)


@mcp.tool()
def download_media(url: str, output_dir: str | None = None, wait: bool = True, timeout: int = 900) -> dict:
    """Download a public video through the installed social-fetch client. Jobs stay in SOCIAL_FETCH_DATA_DIR, default ./mcp-data. A ready file is exported to output_dir or ./mcp-data/downloads. On Vercel, use wait=False and poll media_status."""
    return _service.download_media_job(url, output_dir, wait, timeout)


@mcp.tool()
def export_media(job_id: str, output_path: str) -> dict:
    """Export a ready local job to a new filename. Existing files are not overwritten. The job remains in the data directory."""
    return _service.export_media(job_id, output_path)


@mcp.tool()
def media_status(job_id: str) -> dict:
    """Read a local download job. Status is queued, downloading, assembling, waiting, ready, failed, or cancelled."""
    return _service.media_status(job_id)


@mcp.tool()
def fetch_resource(url: str) -> dict:
    """Save one public linked resource through the local library and return readable text when the library can extract it."""
    return _service.fetch_resource(url)


@mcp.tool()
def search_hashtags(query: str, count: int = 10) -> dict:
    """Search public TikTok videos for a hashtag. This is TikTok-only. A missing SOCIALFETCH_API_KEY returns an error dict and does not pretend to search other platforms."""
    return _service.search_hashtags(query, count)


@mcp.tool()
def search_suggestions(query: str) -> dict:
    """Get TikTok search suggestions. TikTok-only. Missing key returns an error dict and does not call the network."""
    return _service.search_suggestions(query)


@mcp.tool()
def search_shop_products(query: str, count: int = 10) -> dict:
    """Search TikTok Shop products. TikTok-only. Missing key returns an error dict. This does not invent shop search for other platforms."""
    return _service.search_shop_products(query, count)


@mcp.tool()
def get_account_sample(url: str, count: int = 3) -> dict:
    """Read a bounded account sample from the installed library. Coverage depends on the library. It is not a full follower download."""
    return _service.get_account_sample(url, count)

if __name__ == "__main__":
    main()
