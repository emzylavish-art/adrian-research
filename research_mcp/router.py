"""Free-first router for platforms added after the original fourteen.

Returns None when the URL is not one of these platforms, so the existing
tool body stays the path. A useful free result is returned as-is. A miss
falls through only when FREE_ONLY is false and a paid key is present.
"""
from __future__ import annotations

import os
from urllib.parse import urlparse

from research_mcp.backends.linkedin_free import get_profile as linkedin_profile
from research_mcp.backends.odysee_free import get_video as odysee_video
from research_mcp.backends.pinterest_free import get_pin
from research_mcp.backends.rumble_free import get_video as rumble_video
from research_mcp.backends.tiktok_free import get_profile as tiktok_profile
from research_mcp.backends.tiktok_free import get_video as tiktok_video
from research_mcp.util.schema import normalize


def route(tool_name: str, **kwargs) -> dict | None:
    kind = _kind(kwargs.get("url") or "", kwargs.get("platform"))
    if tool_name == "get_profile" and str(kwargs.get("platform") or "").lower() == "linkedin":
        handle = str(kwargs.get("handle") or "").lstrip("@")
        kind = "linkedin"
        kwargs = {**kwargs, "url": f"https://www.linkedin.com/in/{handle}"}
    if tool_name == "get_profile" and str(kwargs.get("platform") or "").lower() == "tiktok":
        kind = "tiktok"
    if tool_name == "get_post" and "tiktok.com" in str(kwargs.get("url") or ""):
        kind = "tiktok"
    if kind is None:
        return None
    result = _call(kind, kwargs.get("url") or "", str(kwargs.get("handle") or ""))
    useful = _useful(result)
    if kind == "tiktok" and not useful and not _blocked():
        return None
    if useful or _blocked() or not _paid_key():
        return _schema(result, kwargs.get("url") or "", kind)
    return None


def _kind(url: str, platform: str | None) -> str | None:
    host = urlparse(url).netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    name = (platform or "").lower()
    if "linkedin.com" in host or name == "linkedin":
        return "linkedin"
    if "pinterest." in host or name == "pinterest":
        return "pinterest"
    if host == "rumble.com" or name == "rumble":
        return "rumble"
    if "odysee.com" in host or url.startswith("lbry://") or name == "odysee":
        return "odysee"
    if "tiktok.com" in host or name == "tiktok":
        return "tiktok"
    return None


def _call(kind: str, url: str, handle: str) -> dict:
    if kind == "tiktok":
        if "/video/" in url or "/photo/" in url:
            return tiktok_video(url)
        return tiktok_profile(handle or url)
    if kind == "linkedin":
        return linkedin_profile(url)
    if kind == "pinterest":
        return get_pin(url)
    if kind == "rumble":
        return rumble_video(url)
    return odysee_video(url)


def _useful(result: dict) -> bool:
    data = result.get("data") if isinstance(result, dict) else None
    if not isinstance(data, dict):
        return False
    return any(data.get(key) for key in ("title", "name", "description", "image_url", "play_count", "play_link", "follower_count", "username"))


def _blocked() -> bool:
    return os.getenv("FREE_ONLY", "").strip().lower() in {"1", "true", "yes"}


def _paid_key() -> bool:
    return bool(os.getenv("SOCIALFETCH_API_KEY") or os.getenv("EASYDOWN_API_KEY"))


def _schema(result: dict, url: str, kind: str) -> dict:
    data = result.get("data") if isinstance(result.get("data"), dict) else {}
    partial = {
        "platform": kind,
        "title": data.get("title") or data.get("name"),
        "description": data.get("description") or data.get("headline") or data.get("recent_activity"),
        "author": {
            "username": data.get("author") or data.get("channel"),
            "display_name": data.get("name") or data.get("channel") or data.get("author"),
            "profile_url": data.get("profile_url"),
        },
        "metrics": {
            "views": data.get("view_count") if data.get("view_count") is not None else data.get("play_count"),
            "likes": data.get("like_count"),
            "comments": data.get("comment_count"),
            "shares": data.get("share_count"),
            "followers": data.get("follower_count") if data.get("follower_count") is not None else data.get("followers"),
        },
        "media": {
            "thumbnail_url": data.get("picture_url") or data.get("image_url"),
            "image_urls": [data["image_url"]] if data.get("image_url") else [],
            "video_urls": [data["play_link"]] if data.get("play_link") else [],
        },
        "path_used": "free",
        "source_detail": result.get("source_name"),
        "credits_charged": 0,
        "errors": list(result.get("errors") or []),
        "raw_platform_data": data,
    }
    return normalize(partial, kind, url, data.get("canonical_url") or url)
