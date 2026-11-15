"""returnyoutubedislike counts only.

GET https://returnyoutubedislikeapi.com/votes?videoId=jNQXAC9IVRw
returned likes and dislikes as JSON numbers on 2026-11-15. This module
does not download files. A missing field stays null.

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
