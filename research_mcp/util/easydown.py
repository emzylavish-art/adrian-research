"""EasyDown client. Paths come from the live OpenAPI, not from a guessed sketch.

Audited 2026-11-15 from https://api.easydown.org/openapi.json:
POST /api/v1/parse
POST /api/v1/platforms/{platform}/parse
Body is {"url": "<public media url>"}. Auth is Authorization: Bearer.
"""
from __future__ import annotations

from research_mcp.util.api import EASYDOWN_BASE, api_post, easydown_key
from research_mcp.util.errors import bad_request

# Path enum from the OpenAPI operation parsePlatformMedia.
EASYDOWN_PLATFORMS = (
    "tiktok",
    "douyin",
    "toutiao",
    "youtube",
    "twitter",
    "instagram",
    "threads",
    "xiaohongshu",
    "bilibili",
    "kuaishou",
    "weibo",
)

# Credits published on the same OpenAPI operation. The response JSON does not
# include a billed-credit field, so tools must not invent credits_charged.
CREDIT_COST = {
    "youtube": 3,
    "threads": 2,
    "kuaishou": 2,
    "xiaohongshu": 10,
}
DEFAULT_CREDIT_COST = 1

SLUGS = {"x": "twitter"}


def easydown_slug(platform: str | None) -> str | None:
    if not platform:
        return None
    slug = SLUGS.get(platform, platform)
    return slug if slug in EASYDOWN_PLATFORMS else None


def easydown_parse(url: str, platform: str | None = None) -> dict:
    """POST a public media URL. platform selects the full-data route."""
    slug = easydown_slug(platform) if platform else None
    if platform and slug is None:
        return bad_request(f"EasyDown has no parse route for {platform}")
    path = f"/api/v1/platforms/{slug}/parse" if slug else "/api/v1/parse"
    return api_post(EASYDOWN_BASE, path, {"url": url}, key=easydown_key())
