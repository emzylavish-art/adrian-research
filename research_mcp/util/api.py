"""REST helper. Keys stay in headers. A missing key does not touch the network."""
from __future__ import annotations

import json
import os
import socket
import urllib.error
import urllib.parse
import urllib.request

from research_mcp.util.errors import (
    api_key_missing,
    auth_failed,
    not_found,
    rate_limited,
    relay_timeout,
    request_failed,
    upstream_error,
)
from research_mcp.util.limits import default_timeout

SOCIALFETCH_BASE = "https://api.socialfetch.dev"
EASYDOWN_BASE = "https://api.easydown.org"


def _header_key(base: str, key: str) -> dict[str, str]:
    if "easydown" in base:
        return {"Authorization": f"Bearer {key}"}
    return {"x-api-key": key}


def _decode(raw: bytes) -> dict:
    if not raw:
        return {}
    parsed = json.loads(raw.decode("utf-8", "replace"))
    return parsed if isinstance(parsed, dict) else {"result": parsed}


def _from_http(exc: urllib.error.HTTPError, base: str) -> dict:
    try:
        body = _decode(exc.read())
    except (OSError, ValueError, UnicodeError):
        body = {}
    err = body.get("error") if isinstance(body.get("error"), dict) else {}
    detail = err.get("message") or body.get("msg") or str(exc.reason)
    status = exc.code
    if status in (401, 403):
        out = auth_failed()
    elif status == 404:
        out = not_found(detail)
    elif status == 429:
        retry_after = exc.headers.get("Retry-After") if exc.headers else None
        try:
            retry_after = int(retry_after) if retry_after else 60
        except (TypeError, ValueError):
            retry_after = 60
        out = rate_limited(retry_after)
    elif status >= 500:
        out = upstream_error(status, detail)
    else:
        out = {"error": err.get("code") or body.get("code") or "request_failed", "detail": detail, "status": status}
    request_id = err.get("requestId")
    if request_id:
        out["requestId"] = request_id
    out["base"] = base
    return out


def _call(method: str, base: str, path: str, *, params=None, body=None, key=None, timeout=None) -> dict:
    if not key:
        return api_key_missing(base)
    timeout = default_timeout("metadata") if timeout is None else timeout
    encoded = {}
    for key_name, value in (params or {}).items():
        if value is None or value is False:
            continue
        encoded[key_name] = "true" if value is True else value
    query = urllib.parse.urlencode(encoded)
    url = base.rstrip("/") + path + (("?" + query) if query else "")
    data = None if body is None else json.dumps(body).encode("utf-8")
    headers = {
        "Accept": "application/json",
        "User-Agent": "tiktok-research-mcp/1.0",
        **_header_key(base, key),
    }
    if data is not None:
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return _decode(response.read())
    except urllib.error.HTTPError as exc:
        return _from_http(exc, base)
    except (urllib.error.URLError, TimeoutError, socket.timeout) as exc:
        return relay_timeout(str(getattr(exc, "reason", exc)))
    except (ValueError, UnicodeError) as exc:
        return request_failed(str(exc))


def api_get(base: str, path: str, params=None, key=None, timeout=None) -> dict:
    return _call("GET", base, path, params=params, key=key, timeout=timeout)


def api_post(base: str, path: str, body: dict, key=None, timeout=None) -> dict:
    return _call("POST", base, path, body=body, key=key, timeout=timeout)


def socialfetch_key() -> str | None:
    return os.getenv("SOCIALFETCH_API_KEY") or None


def easydown_key() -> str | None:
    return os.getenv("EASYDOWN_API_KEY") or None
