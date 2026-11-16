"""Pinterest pin lookup.

The installed social-fetch package has no Nitrograph pin endpoint.
It calls https://www.pinterest.com/resource/PinResource/get/ from
pinterest_download. This module uses that same public JSON call.
If the pin id is missing or the JSON has no fields, it falls through
to Client.resource and reads only tags that are actually present.

Breaks when Pinterest retires PinResource/get or stops putting the
title on resource_response.data. Do not invent a board or author.
"""
from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
import urllib.error

from research_mcp.backends import envelope
from research_mcp.util.errors import not_found, request_failed

_PIN = re.compile(r"/pin/(\d+)")


def get_pin(url: str) -> dict:
    checked = (url or "").strip()
    match = _PIN.search(checked)
    if not match:
        return _from_resource(checked, [request_failed("pinterest pin id was not in the URL")])
    query = urllib.parse.urlencode({
        "data": json.dumps({"options": {"id": match.group(1), "field_set_key": "detailed"}}),
    })
    request = urllib.request.Request(
        "https://www.pinterest.com/resource/PinResource/get/?" + query,
        headers={"User-Agent": "adrian-research/1.0", "X-Pinterest-PWS-Handler": "www/[username].js"},
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            payload = json.loads(response.read(250000).decode("utf-8", "replace"))
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return envelope({}, "pinterest-pinresource", [not_found("pinterest pin")])
        return _from_resource(checked, [request_failed(f"PinResource HTTP {exc.code}")])
    except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
        return _from_resource(checked, [request_failed(type(exc).__name__)])
    pin = ((payload.get("resource_response") or {}).get("data") or {})
    if not isinstance(pin, dict) or not pin:
        return _from_resource(checked, [not_found("pinterest pin")])
    errors = []
    image = None
    images = pin.get("images") if isinstance(pin.get("images"), dict) else {}
    for key in ("orig", "736x", "474x"):
        item = images.get(key)
        if isinstance(item, dict) and item.get("url"):
            image = item["url"]
            break
    data = {
        "title": pin.get("title") or pin.get("grid_title") or None,
        "description": pin.get("description") or None,
        "image_url": image,
        "author": ((pin.get("pinner") or {}).get("username") if isinstance(pin.get("pinner"), dict) else None),
        "board": ((pin.get("board") or {}).get("name") if isinstance(pin.get("board"), dict) else None),
    }
    for field in ("title", "description", "image_url", "author", "board"):
        if not data[field]:
            errors.append({"error": "missing_field", "detail": f"PinResource had no {field}"})
    return envelope(data, "pinterest-pinresource", errors)


def _from_resource(url: str, errors: list) -> dict:
    try:
        from research_mcp.backends.socialfetch_local import resource
    except Exception as exc:
        errors.append(request_failed(type(exc).__name__))
        return envelope({}, "pinterest-resource", errors)
    saved = resource(url)
    text = ""
    if isinstance(saved, dict):
        text = saved.get("text_preview") or ""
        if saved.get("error") or saved.get("status") not in (None, "ready"):
            errors.append(saved if saved.get("error") else request_failed(str(saved.get("message") or saved.get("status"))))
    title = _meta(text, "og:title")
    data = {
        "title": title,
        "description": _meta(text, "og:description"),
        "image_url": _meta(text, "og:image"),
        "author": None,
        "board": None,
    }
    if not title:
        errors.append({"error": "missing_field", "detail": "pinterest resource text had no title"})
    return envelope(data, "pinterest-resource", errors)


def _meta(text: str, name: str) -> str | None:
    match = re.search(rf'{name}["\s:]+([^"<\n]+)', text or "", re.I)
    return match.group(1).strip() or None if match else None
