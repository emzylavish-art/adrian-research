"""Keyless YouTube metadata and counts.

GET https://returnyoutubedislikeapi.com/votes?videoId=jNQXAC9IVRw
returned likes and dislikes as JSON numbers on 2026-11-15. This module
also reads YouTube oEmbed for title/author and the public watch page for
views. It does not download files. A missing field stays null.

get_post calls get_metadata and get_counts when EASYDOWN_API_KEY is absent.
A present key keeps the existing EasyDown lookup and does not call this
module.

Breaks when that votes path or the likes/dislikes keys change.
"""
from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
import urllib.error

from research_mcp.backends import envelope
from research_mcp.util.errors import request_failed

_ID = re.compile(r"(?:v=|youtu\.be/|shorts/)([\w-]{6,})")
_VIEWS = re.compile(r'"text":"([0-9][0-9,\.\s]*) views"', re.I)


def get_metadata(url: str) -> dict:
    """Read title/author from public YouTube oEmbed and views from watch HTML."""
    identity = _identity(url)
    if not identity:
        return envelope({}, "youtube-oembed-page", [request_failed("video id was not in the input")])
    errors = []
    data = {"video_id": identity, "title": None, "author": None, "author_url": None, "view_count": None}
    oembed_url = "https://www.youtube.com/oembed?" + urllib.parse.urlencode({"url": _watch_url(identity), "format": "json"})
    try:
        request = urllib.request.Request(oembed_url, headers={"User-Agent": "adrian-research/1.0"})
        with urllib.request.urlopen(request, timeout=20) as response:
            payload = json.loads(response.read(100000).decode("utf-8", "replace"))
        if isinstance(payload, dict):
            data["title"] = payload.get("title")
            data["author"] = payload.get("author_name")
            data["author_url"] = payload.get("author_url")
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
        errors.append(request_failed(f"YouTube oEmbed: {type(exc).__name__}"))
    try:
        request = urllib.request.Request(_watch_url(identity), headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(request, timeout=20) as response:
            html = response.read(5000000).decode("utf-8", "replace")
        match = _VIEWS.search(html)
        if match:
            data["view_count"] = int(re.sub(r"[^0-9]", "", match.group(1)))
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
        errors.append(request_failed(f"YouTube watch page: {type(exc).__name__}"))
    for field in ("title", "author", "view_count"):
        if data[field] is None:
            errors.append({"error": "missing_field", "detail": f"youtube-oembed-page had no {field}"})
    return envelope(data, "youtube-oembed-page", errors)


def get_counts(video_id: str) -> dict:
    identity = _identity(video_id)
    if not identity:
        return envelope({}, "returnyoutubedislike", [request_failed("video id was not in the input")])
    query = urllib.parse.urlencode({"videoId": identity})
    request = urllib.request.Request(
        "https://returnyoutubedislikeapi.com/votes?" + query,
        headers={"User-Agent": "adrian-research/1.0"},
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            payload = json.loads(response.read(100000).decode("utf-8", "replace"))
    except urllib.error.HTTPError as exc:
        return envelope({}, "returnyoutubedislike", [request_failed(f"HTTP {exc.code}")])
    except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
        return envelope({}, "returnyoutubedislike", [request_failed(type(exc).__name__)])
    if not isinstance(payload, dict):
        return envelope({}, "returnyoutubedislike", [request_failed("votes response was not an object")])
    likes = payload.get("likes") if isinstance(payload.get("likes"), int) else None
    dislikes = payload.get("dislikes") if isinstance(payload.get("dislikes"), int) else None
    errors = []
    if likes is None:
        errors.append({"error": "missing_field", "detail": "returnyoutubedislike had no likes"})
    if dislikes is None:
        errors.append({"error": "missing_field", "detail": "returnyoutubedislike had no dislikes"})
    return envelope({"video_id": identity, "likes": likes, "dislikes": dislikes}, "returnyoutubedislike", errors)


def _identity(value: str) -> str | None:
    text = (value or "").strip()
    if re.fullmatch(r"[\w-]{6,}", text):
        return text
    match = _ID.search(text)
    return match.group(1) if match else None


def _watch_url(identity: str) -> str:
    return "https://www.youtube.com/watch?v=" + urllib.parse.quote(identity)
