"""Free public backends. None of these modules read API keys."""
from __future__ import annotations


def envelope(data: dict | None, source_name: str, errors: list | None = None) -> dict:
    return {
        "data": data or {},
        "source_name": source_name,
        "path_used": "free",
        "credits_charged": 0,
        "errors": list(errors or []),
    }
