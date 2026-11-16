"""One output shape for every info-returning tool."""
from __future__ import annotations

import copy

BASE_SCHEMA = {
    "platform": None,
    "url": None,
    "canonical_url": None,
    "content_type": None,
    "title": None,
    "description": None,
    "author": {
        "username": None,
        "display_name": None,
        "bio": None,
        "followers": None,
        "verified": None,
        "avatar_url": None,
        "profile_url": None,
    },
    "created_at": None,
    "metrics": {
        "views": None,
        "likes": None,
        "comments": None,
        "shares": None,
        "saves": None,
        "reposts": None,
    },
    "media": {
        "thumbnail_url": None,
        "video_urls": [],
        "image_urls": [],
        "audio_urls": [],
        "duration_ms": None,
        "width": None,
        "height": None,
    },
    "transcript": None,
    "comments_preview": [],
    "hashtags": [],
    "music": None,
    "location": None,
    "is_ad": None,
    "raw_platform_data": None,
    "credits_charged": 0,
    "path_used": None,
    "source_detail": None,
    "errors": [],
}


def normalize(partial: dict | None, platform: str | None, url: str, canonical: str, errors: list | None = None) -> dict:
    """Deep-merge a partial result into BASE_SCHEMA. Every schema key is present."""
    out = copy.deepcopy(BASE_SCHEMA)
    incoming = partial or {}
    for key in ("author", "metrics", "media"):
        value = incoming.get(key)
        if isinstance(value, dict):
            out[key].update(value)
    for key, value in incoming.items():
        if key not in ("author", "metrics", "media"):
            out[key] = value
    merged_errors = []
    if isinstance(out.get("errors"), list):
        merged_errors.extend(out["errors"])
    if errors:
        merged_errors.extend(errors)
    out["errors"] = merged_errors
    out["platform"] = platform if platform is not None else incoming.get("platform")
    out["url"] = url
    out["canonical_url"] = incoming.get("canonical_url") or canonical or url
    if not isinstance(out.get("credits_charged"), int):
        try:
            out["credits_charged"] = int(out.get("credits_charged") or 0)
        except (TypeError, ValueError):
            out["credits_charged"] = 0
    for key, default in BASE_SCHEMA.items():
        out.setdefault(key, copy.deepcopy(default))
    return out
