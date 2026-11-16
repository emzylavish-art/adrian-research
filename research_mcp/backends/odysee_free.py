"""Odysee public JSON-RPC.

api.odysee.com/api/v1/proxy returned 404 on 2026-11-15.
api.na-backend.odysee.com/api/v1/proxy answered resolve and claim_search.
View count was not in the claim_search meta keys observed that day.
This module leaves it null and records the missing field. It does not
invent a number.

Breaks when the na-backend proxy path or claim_search item shape changes.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request

from research_mcp.backends import envelope
from research_mcp.util.errors import not_found, request_failed

_API = "https://api.na-backend.odysee.com/api/v1/proxy"


def get_video(url: str) -> dict:
    checked = (url or "").strip()
    if not checked:
        return envelope({}, "odysee-proxy", [request_failed("url is required")])
    payload = _call("resolve", {"urls": [checked]})
    claim = _first_claim(payload)
    if claim is None:
        payload = _call("claim_search", {"text": checked, "page_size": 1})
        items = ((payload.get("result") or {}).get("items") or []) if isinstance(payload, dict) else []
        claim = items[0] if items and isinstance(items[0], dict) else None
    if not isinstance(claim, dict):
        detail = payload.get("error") if isinstance(payload, dict) else "no claim"
        return envelope({}, "odysee-proxy", [not_found(str(detail or "odysee claim"))])
    value = claim.get("value") if isinstance(claim.get("value"), dict) else {}
    channel = claim.get("signing_channel") if isinstance(claim.get("signing_channel"), dict) else {}
    channel_value = channel.get("value") if isinstance(channel.get("value"), dict) else {}
    views = _views(claim)
    data = {
        "title": value.get("title") or claim.get("name") or None,
        "channel": channel_value.get("title") or channel.get("name") or None,
        "view_count": views,
        "description": value.get("description") or None,
        "canonical_url": claim.get("canonical_url") or claim.get("permanent_url") or checked,
    }
    errors = []
    if views is None:
        errors.append({"error": "missing_field", "detail": "odysee claim_search meta had no view count"})
    for field in ("title", "channel", "description"):
        if not data[field]:
            errors.append({"error": "missing_field", "detail": f"odysee claim had no {field}"})
    return envelope(data, "odysee-proxy", errors)


def _call(method: str, params: dict) -> dict:
    body = json.dumps({"method": method, "params": params}).encode()
    request = urllib.request.Request(
        _API,
        data=body,
        headers={"User-Agent": "adrian-research/1.0", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            parsed = json.loads(response.read(300000).decode("utf-8", "replace"))
    except urllib.error.HTTPError as exc:
        return {"error": f"HTTP {exc.code}"}
    except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
        return {"error": type(exc).__name__}
    return parsed if isinstance(parsed, dict) else {"error": "odysee response was not an object"}


def _first_claim(payload: dict) -> dict | None:
    result = payload.get("result") if isinstance(payload, dict) else None
    if not isinstance(result, dict):
        return None
    for value in result.values():
        if isinstance(value, dict) and (value.get("value") or value.get("claim_id")):
            return value
    return None


def _views(claim: dict) -> int | None:
    meta = claim.get("meta") if isinstance(claim.get("meta"), dict) else {}
    for key in ("view_count", "views", "reposted"):
        value = meta.get(key)
        if isinstance(value, int) and key != "reposted":
            return value
    return None
