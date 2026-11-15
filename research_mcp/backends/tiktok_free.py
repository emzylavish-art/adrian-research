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
    if isinstance(modules, dict) and "videos" not in modules:
        return modules
    try:
        ref = modules["refs"].resolve_video(url)
        details = modules["videos"].get_details(ref)
        media = modules["videos"].get_media(ref)
    except Exception as exc:
        return envelope({}, "omkarcloud-tiktok", [request_failed(f"{type(exc).__name__}: {exc}")])
    if not isinstance(details, dict):
        return envelope({}, "omkarcloud-tiktok", [request_failed("video details were not a dict")])
    stats = details.get("stats") if isinstance(details.get("stats"), dict) else {}
    author = details.get("author") if isinstance(details.get("author"), dict) else {}
    author_stats = details.get("author_stats") if isinstance(details.get("author_stats"), dict) else {}
    video = {}
    if isinstance(media, dict) and isinstance(media.get("video"), dict):
        video = media["video"]
    elif isinstance(details.get("video"), dict):
        video = details["video"]
    duration = video.get("duration_seconds")
    duration_ms = int(duration * 1000) if isinstance(duration, (int, float)) else None
    data = {
        "title": details.get("title"),
        "description": details.get("description"),
        "author": author.get("username"),
        "display_name": author.get("nickname"),
        "bio": author.get("biography"),
        "followers": _int(author_stats.get("follower_count")),
        "verified": author.get("is_verified") if isinstance(author.get("is_verified"), bool) else None,
        "avatar_url": author.get("profile_picture"),
        "profile_url": author.get("link"),
        "created_at": details.get("created_at"),
        "play_count": _int(stats.get("play_count")),
        "like_count": _int(stats.get("like_count")),
        "comment_count": _int(stats.get("comment_count")),
        "share_count": _int(stats.get("share_count")),
        "save_count": _int(stats.get("save_count")),
        "repost_count": _int(stats.get("repost_count")),
        "play_link": video.get("play_link"),
        "download_link": video.get("download_link"),
        "cover": details.get("cover") or video.get("cover"),
        "duration_ms": duration_ms,
        "width": _int(video.get("width")),
        "height": _int(video.get("height")),
    }
    errors = _missing(data, ("play_count", "like_count", "comment_count", "share_count", "play_link"))
    return envelope(data, "omkarcloud-tiktok", errors)


def get_profile(handle: str) -> dict:
    modules = _modules()
    if isinstance(modules, dict) and "users" not in modules:
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
        from tiktok import refs, users, videos
    except Exception as exc:
        return envelope({}, "omkarcloud-tiktok", [request_failed(f"tiktok scraper is not importable: {type(exc).__name__}")])
    return {"refs": refs, "users": users, "videos": videos}


def _int(value):
    return value if isinstance(value, int) else None


def _missing(data: dict, fields: tuple[str, ...]) -> list:
    return [
        {"error": "missing_field", "detail": f"omkarcloud-tiktok had no {field}"}
        for field in fields
        if data.get(field) in (None, "")
    ]
