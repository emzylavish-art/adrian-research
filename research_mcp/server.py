"""Adrian Research MCP.

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
    # Renamed by request. The constructor flags, host, and port stay the same.
    "adrian-research",
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
    # Presence only. Never print a key value.
    print("SOCIALFETCH_API_KEY", "present" if os.getenv("SOCIALFETCH_API_KEY") else "absent")
    print("EASYDOWN_API_KEY", "present" if os.getenv("EASYDOWN_API_KEY") else "absent")
    mcp.run(transport=os.getenv("MCP_TRANSPORT", "stdio"))


# Appended universal social layer.
# search_videos, the _VIDEO regex, and FootageSearch.from_env stay as they were.
# The server name and the key-presence lines in main() were changed because the
# repository was renamed to adrian-research. This block sits before the
# unchanged `if __name__` guard so registration runs before mcp.run().
from research_mcp.util import service as _service
from research_mcp.router import route as _route


@mcp.tool()
def get_post(
    url: str,
    include_transcript: bool = False,
    include_comments: bool = False,
    download_media: bool = False,
) -> dict:
    """Look up one public post from any supported platform. Returns the same shape every time. Read errors before treating empty fields as real data. download_media writes a local job under the data directory and can take several minutes."""
    # FREE-FIRST: only LinkedIn, Pinterest, Rumble, and Odysee are claimed here.
    # Other URLs return None and keep the existing lookup.
    routed = _route("get_post", url=url, include_transcript=include_transcript, include_comments=include_comments, download_media=download_media)
    if routed is not None:
        return routed
    return _service.get_post(url, include_transcript, include_comments, download_media)


@mcp.tool()
def search_posts(query: str, platform: str | None = None, count: int = 10) -> list:
    """Search indexed public posts. platform restricts the search. When omitted, every social-fetch source is queried and the merged list is capped at 20. This does not change search_videos."""
    return _service.search_posts(query, platform, count, search=_search)


@mcp.tool()
def get_profile(handle: str, platform: str) -> dict:
    """Get a public profile card. TikTok and Bluesky use Social Fetch REST when SOCIALFETCH_API_KEY is set. Other library platforms return a bounded account sample, not a full profile."""
    # FREE-FIRST: a LinkedIn handle uses the guest HTML reader before any paid call.
    routed = _route("get_profile", handle=handle, platform=platform)
    if routed is not None:
        return routed
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


# Next TikTok tools, appended below the universal layer.
# search_videos, the FastMCP constructor, host, port, transport, and main()
# are not modified. This block stays above the unchanged entry guard.

from research_mcp.util import tiktok as _tiktok


@mcp.tool()
def search_tiktok_videos(query: str, date_posted: str | None = None, sort_by: str | None = None, region: str | None = None, cursor: str | None = None) -> dict:
    """Search TikTok's own video index. This does not call or replace search_videos. Read credits_charged from the response. A missing key returns an error and does not call the network."""
    return _tiktok.search_tiktok_videos(query, date_posted, sort_by, region, cursor)


@mcp.tool()
def search_tiktok_top(query: str, date_posted: str | None = None, sort_by: str | None = None, region: str | None = None, cursor: str | None = None) -> dict:
    """Search TikTok Top results, including photo posts. Videos-only search is search_tiktok_videos. This does not replace search_videos."""
    return _tiktok.search_tiktok_top(query, date_posted, sort_by, region, cursor)


@mcp.tool()
def search_tiktok_users(query: str, cursor: str | None = None) -> dict:
    """Search public TikTok users. Results use the documented users array. Missing key returns an error dict."""
    return _tiktok.search_tiktok_users(query, cursor)


@mcp.tool()
def list_tiktok_followers(handle: str, cursor: str | None = None, user_id: str | None = None) -> dict:
    """List one page of public TikTok followers. hidden, private, and not_found come back in errors. Do not treat an empty page as a full follower download."""
    return _tiktok.list_tiktok_followers(handle, cursor, user_id)


@mcp.tool()
def list_tiktok_following(handle: str, cursor: str | None = None) -> dict:
    """List one page of public TikTok accounts a profile follows. A hidden list returns an error entry, not a crash."""
    return _tiktok.list_tiktok_following(handle, cursor)


@mcp.tool()
def get_tiktok_region(handle: str) -> dict:
    """Look up the public region record for a TikTok handle. The billed amount is credits_charged when the response includes it."""
    return _tiktok.get_tiktok_region(handle)


@mcp.tool()
def get_tiktok_audience(handle: str, confirm: bool = False) -> dict:
    """Look up a TikTok audience report. The catalog lists 30 credits. The call does not run unless confirm=True. credits_charged still comes from the response, not from that catalog number."""
    return _tiktok.get_tiktok_audience(handle, confirm)


@mcp.tool()
def get_tiktok_engagement(handle: str, confirm: bool = False) -> dict:
    """Look up a TikTok engagement audit. The catalog lists 5 credits. The call does not run unless confirm=True."""
    return _tiktok.get_tiktok_engagement(handle, confirm)


@mcp.tool()
def get_tiktok_live(handle: str) -> dict:
    """Look up whether a TikTok handle is live. Use get_tiktok_live_info with the returned room id and user id for the room record."""
    return _tiktok.get_tiktok_live(handle)


@mcp.tool()
def get_tiktok_live_info(room_id: str, user_id: str) -> dict:
    """Get one TikTok live room. Both room_id and user_id are required by the documented route."""
    return _tiktok.get_tiktok_live_info(room_id, user_id)


@mcp.tool()
def get_tiktok_hosted_media(url: str, region: str | None = None, confirm: bool = False) -> dict:
    """Ask Social Fetch to host a TikTok file. The catalog lists 11 credits when media is returned. This is not download_media, and it does not run unless confirm=True."""
    return _tiktok.get_tiktok_hosted_media(url, region, confirm)


@mcp.tool()
def list_tiktok_collection(url: str, cursor: str | None = None) -> dict:
    """List videos in a public TikTok collection URL. This route has no lookupStatus. An empty list is not proof the collection is missing."""
    return _tiktok.list_tiktok_collection(url, cursor)


@mcp.tool()
def get_tiktok_song(song_id: str) -> dict:
    """Get one TikTok sound by the id from a music URL or a video's music.id. Do not pass the whole music URL as the id."""
    return _tiktok.get_tiktok_song(song_id)


@mcp.tool()
def list_tiktok_sound_videos(clip_id: str, cursor: str | None = None) -> dict:
    """List public videos using a TikTok music clip id. An empty page has no lookupStatus on this route."""
    return _tiktok.list_tiktok_sound_videos(clip_id, cursor)


@mcp.tool()
def list_tiktok_store_products(url: str, cursor: str | None = None, region: str | None = None, sort_by: str | None = None) -> dict:
    """List products in a public TikTok Shop store URL. region must be one of the documented shop catalogs. US is the upstream default when omitted."""
    return _tiktok.list_tiktok_store_products(url, cursor, region, sort_by)


@mcp.tool()
def get_tiktok_product(url: str, region: str | None = None) -> dict:
    """Get one TikTok Shop product from its public product URL. This does not search the catalog."""
    return _tiktok.get_tiktok_product(url, region)


@mcp.tool()
def list_tiktok_product_reviews(url: str | None = None, product_id: str | None = None, region: str | None = None, page: int | None = None) -> dict:
    """List TikTok Shop reviews. Provide the product URL or the product id. Pagination is page-based."""
    return _tiktok.list_tiktok_product_reviews(url, product_id, region, page)


@mcp.tool()
def list_tiktok_showcase(handle: str, cursor: str | None = None, region: str | None = None) -> dict:
    """List products showcased on a TikTok profile. An empty list has no lookupStatus. Call get_profile first if you need to know whether the profile exists."""
    return _tiktok.list_tiktok_showcase(handle, cursor, region)


@mcp.tool()
def get_tiktok_ad(ad_id: str | None = None, url: str | None = None) -> dict:
    """Get one public TikTok Ad Library or Top Ads record by ad id or detail URL."""
    return _tiktok.get_tiktok_ad(ad_id, url)


@mcp.tool()
def search_tiktok_ads(query: str | None = None, advertiser_name: str | None = None, advertiser_business_id: str | None = None, country: str | None = None, start_date: str | None = None, end_date: str | None = None, cursor: str | None = None) -> dict:
    """Search the public TikTok Ad Library. US is not a supported country. advertiser_business_id requires advertiser_name. Dates must be sent together as YYYY-MM-DD."""
    return _tiktok.search_tiktok_ads(query, advertiser_name, advertiser_business_id, country, start_date, end_date, cursor)

if __name__ == "__main__":
    main()
