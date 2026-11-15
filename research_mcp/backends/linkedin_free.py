"""Guest LinkedIn profile HTML.

Wraps the fail-closed contract of aadisriram/nodejs-linkedin-scraper:
one fetch, no retry, no proxy pool. HTTP 429 and 999 are terminal.
An auth wall is terminal. The MCP server is Python, so this module
parses the public meta tags itself instead of requiring Node.

Breaks when LinkedIn replaces public_profile_v3 HTML with an auth wall
or stops emitting og:title. Do not retry those responses.
"""
from __future__ import annotations

import html
import re
import urllib.error
import urllib.request

from research_mcp.backends import envelope
from research_mcp.util.errors import not_found, rate_limited, request_failed

_TITLE = re.compile(r'<meta[^>]+property="og:title"[^>]+content="([^"]*)"', re.I)
_DESC = re.compile(r'<meta[^>]+property="og:description"[^>]+content="([^"]*)"', re.I)
_IMAGE = re.compile(r'<meta[^>]+property="og:image"[^>]+content="([^"]*)"', re.I)


def get_profile(url: str) -> dict:
    checked = (url or "").strip()
    if "linkedin.com/in/" not in checked:
        return envelope({}, "linkedin-guest", [request_failed("not a public LinkedIn profile URL")])
    request = urllib.request.Request(checked, headers={"User-Agent": "adrian-research/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            status = response.status
            final = response.geturl()
            body = response.read(250000).decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        if exc.code in (429, 999):
            return envelope({}, "linkedin-guest", [rate_limited()])
        if exc.code == 404:
            return envelope({}, "linkedin-guest", [not_found("linkedin profile")])
        return envelope({}, "linkedin-guest", [request_failed(f"HTTP {exc.code}")])
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return envelope({}, "linkedin-guest", [request_failed(type(exc).__name__)])
    if status in (429, 999):
        return envelope({}, "linkedin-guest", [rate_limited()])
    lowered = body.lower()
    if "authwall" in lowered or "/login" in final or "captcha" in lowered and "og:title" not in lowered:
        return envelope({}, "linkedin-guest", [{"error": "blocked", "detail": "linkedin auth wall"}])
    title = html.unescape(_TITLE.search(body).group(1)) if _TITLE.search(body) else ""
    name, headline = _split_title(title)
    description = html.unescape(_DESC.search(body).group(1)) if _DESC.search(body) else None
    image = _IMAGE.search(body).group(1) if _IMAGE.search(body) else None
    errors = []
    if not name:
        errors.append({"error": "missing_field", "detail": "linkedin-guest had no name in og:title"})
    data = {
        "name": name or None,
        "headline": headline,
        "company": None,
        "role": headline,
        "location": None,
        "followers": None,
        "education": None,
        "recent_activity": description,
        "picture_url": image,
        "profile_url": final,
    }
    if data["followers"] is None:
        errors.append({"error": "missing_field", "detail": "linkedin-guest HTML did not expose followers"})
    return envelope(data, "linkedin-guest", errors)


def _split_title(title: str) -> tuple[str, str | None]:
    text = title.replace(" | LinkedIn", "").strip()
    if " - " not in text:
        return text, None
    name, headline = text.split(" - ", 1)
    return name.strip(), headline.strip() or None
