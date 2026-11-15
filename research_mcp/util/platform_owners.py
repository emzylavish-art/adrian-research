"""Which backend owns which platform.

Omniget's PLATFORM-OWNERS.md is an opt-out notice to site owners, not a routing
table. This module is the routing manifest the blueprint asked for. It is the
source of truth for appended tools. It does not copy Omniget code.

Richer public metadata is preferred over a local text extract. A missing key
falls through. It does not crash the server.
"""
from __future__ import annotations

SOCIAL_FETCH_DOWNLOAD = {
    "youtube", "instagram", "tiktok", "x", "facebook", "reddit",
    "bluesky", "pinterest", "twitch", "snapchat", "linkedin", "mastodon",
}
SOCIAL_FETCH_SEARCH = SOCIAL_FETCH_DOWNLOAD
SOCIAL_FETCH_COMMENTS = {"instagram", "reddit"}
SOCIAL_FETCH_IMAGES = {"reddit"}
SOCIALFETCH_REST = {"tiktok", "bluesky"}

PROFILE_URLS = {
    "tiktok": "https://www.tiktok.com/@{handle}",
    "youtube": "https://www.youtube.com/@{handle}",
    "instagram": "https://www.instagram.com/{handle}/",
    "x": "https://x.com/{handle}",
    "facebook": "https://www.facebook.com/{handle}",
    "reddit": "https://www.reddit.com/user/{handle}",
    "bluesky": "https://bsky.app/profile/{handle}",
    "threads": "https://www.threads.net/@{handle}",
}


def metadata_backends(platform: str) -> list[str]:
    order = []
    if platform in SOCIALFETCH_REST:
        order.append("socialfetch_rest")
    from research_mcp.util.easydown import easydown_slug

    if easydown_slug(platform):
        order.append("easydown")
    if platform in SOCIAL_FETCH_DOWNLOAD:
        order.append("social_fetch")
    return order


def profile_url(platform: str, handle: str) -> str | None:
    template = PROFILE_URLS.get(platform)
    if not template or not handle:
        return None
    return template.format(handle=handle.lstrip("@"))
