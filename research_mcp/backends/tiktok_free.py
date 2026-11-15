"""omkarcloud/tiktok-scraper, only the calls Phase 0 observed live.

Verified on 2026-11-15: tiktok.videos.get_details, get_media, and
tiktok.users.get_profile. Search, trending, comments, and ads exist in
that repo and were not live-hit, so this wrapper does not expose them.

The scraper is a source tree, not an installed package. Set
TIKTOK_SCRAPER_HOME to the clone root, or place it at
../tiktok-scraper. If the import fails, this module returns a typed
error and does not invent counts.

Breaks when the scraper renames stats.play_count, video.play_link, or
stats.follower_count, or when its unsigned web requests start failing.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

from research_mcp.backends import envelope
from research_mcp.util.errors import request_failed


def get_video(url: str) -> dict:
    modules = _modules()
    if isinstance(modules, dict):
        return modules
    try:
        details = modules["videos"].get_details(url)
        media = modules["videos"].get_media(url)
    except Exception as exc:
        return envelope({}, "omkarcloud-tiktok", [request_failed(f"{type(exc).__name__}: {exc}")])
    stats = details.get("stats") if isinstance(details, dict) else {}
    video = media.get("video") if isinstance(media, dict) else {}
    stats = stats if isinstance(stats, dict) else {}
    video = video if isinstance(video, dict) else {}
    data = {
        "play_count": _int(stats.get("play_count")),
        "like_count": _int(stats.get("like_count")),
        "comment_count": _int(stats.get("comment_count")),
        "share_count": _int(stats.get("share_count")),
        "play_link": video.get("play_link"),
        "download_link": video.get("download_link"),
        "caption": details.get("caption") or details.get("desc") if isinstance(details, dict) else None,
        "author": (details.get("author") or {}).get("username") if isinstance(details, dict) and isinstance(details.get("author"), dict) else None,
    }
    errors = _missing(data, ("play_count", "like_count", "comment_count", "share_count", "play_link"))
    return envelope(data, "omkarcloud-tiktok", errors)


def get_profile(handle: str) -> dict:
    modules = _modules()
    if isinstance(modules, dict):
        return modules
    try:
        profile = modules["users"].get_profile(handle)
    except Exception as exc:
        return envelope({}, "omkarcloud-tiktok", [request_failed(f"{type(exc).__name__}: {exc}")])
    stats = profile.get("stats") if isinstance(profile, dict) else {}
    stats = stats if isinstance(stats, dict) else {}
    data = {
        "username": profile.get("username") if isinstance(profile, dict) else None,
        "follower_count": _int(stats.get("follower_count")),
        "following_count": _int(stats.get("following_count")),
        "video_count": _int(stats.get("video_count")),
        "verified": profile.get("verified") if isinstance(profile, dict) else None,
    }
    errors = _missing(data, ("username", "follower_count"))
    return envelope(data, "omkarcloud-tiktok", errors)


def _modules():
    root = os.getenv("TIKTOK_SCRAPER_HOME")
    if not root:
        candidate = Path(__file__).resolve().parents[3] / "tiktok-scraper"
        root = str(candidate) if candidate.is_dir() else ""
    if root and root not in sys.path:
        sys.path.insert(0, root)
    try:
        from tiktok import users, videos
    except Exception as exc:
        return envelope({}, "omkarcloud-tiktok", [request_failed(f"tiktok scraper is not importable: {type(exc).__name__}")])
    return {"users": users, "videos": videos}


def _int(value):
    return value if isinstance(value, int) else None


def _missing(data: dict, fields: tuple[str, ...]) -> list:
    return [
        {"error": "missing_field", "detail": f"omkarcloud-tiktok had no {field}"}
        for field in fields
        if data.get(field) in (None, "")
    ]
