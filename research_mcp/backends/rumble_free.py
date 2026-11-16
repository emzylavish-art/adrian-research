"""Rumble public page text.

Uses social-fetch Client.resource. A Cloudflare challenge, 403, or
empty page is a typed block. View count stays null unless the saved
text actually contains it.

Breaks when Rumble puts the title only in a script the resource
reader strips, or when the challenge page replaces the video HTML.
"""
from __future__ import annotations

import re

from research_mcp.backends import envelope
from research_mcp.backends.socialfetch_local import resource
from research_mcp.util.errors import request_failed

_VIEWS = re.compile(r"([0-9][0-9,]*)\s+views", re.I)


def get_video(url: str) -> dict:
    checked = (url or "").strip()
    if "rumble.com" not in checked:
        return envelope({}, "rumble-resource", [request_failed("not a rumble URL")])
    saved = resource(checked)
    text = ""
    errors = []
    if not isinstance(saved, dict):
        return envelope({}, "rumble-resource", [request_failed("resource did not return an object")])
    if saved.get("error"):
        errors.append(saved)
    message = str(saved.get("message") or "")
    text = saved.get("text_preview") or ""
    blob = f"{message}\n{text}".lower()
    if saved.get("status") not in (None, "ready") or "just a moment" in blob or "cloudflare" in blob:
        errors.append({"error": "blocked", "detail": "rumble returned a challenge page, not a video document"})
        return envelope(_empty(), "rumble-resource", errors)
    title = _line(text, "title") or _meta(text, "og:title")
    channel = _line(text, "channel") or _meta(text, "og:site_name")
    description = _meta(text, "og:description")
    uploaded = _meta(text, "uploadDate") or _meta(text, "article:published_time")
    views = None
    match = _VIEWS.search(text)
    if match:
        try:
            views = int(match.group(1).replace(",", ""))
        except ValueError:
            views = None
    data = {
        "title": title,
        "channel": channel,
        "view_count": views,
        "description": description,
        "upload_date": uploaded,
    }
    for field, source in (
        ("title", "rumble resource text"),
        ("channel", "rumble resource text"),
        ("view_count", "rumble resource text"),
        ("description", "rumble resource text"),
        ("upload_date", "rumble resource text"),
    ):
        if data[field] in (None, ""):
            errors.append({"error": "missing_field", "detail": f"{source} had no {field}"})
    return envelope(data, "rumble-resource", errors)


def _empty() -> dict:
    return {"title": None, "channel": None, "view_count": None, "description": None, "upload_date": None}


def _meta(text: str, name: str) -> str | None:
    match = re.search(rf"{re.escape(name)}[^A-Za-z0-9]{{0,12}}([^<\n\"]+)", text or "", re.I)
    return match.group(1).strip() or None if match else None


def _line(text: str, label: str) -> str | None:
    match = re.search(rf"^{label}:\s*(.+)$", text or "", re.I | re.M)
    return match.group(1).strip() or None if match else None
