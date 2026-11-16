"""Thin wrapper over the installed social-fetch Client.

No API key is read. The Client methods stay unchanged.
Breaks when the installed signatures for resource, download,
account, or download_image change.
"""
from __future__ import annotations

import os

from research_mcp.backends import envelope
from research_mcp.util.errors import request_failed

_client = None


def _library():
    global _client
    if _client is None:
        from social_fetch import Client

        _client = Client(
            data_dir=os.getenv("SOCIAL_FETCH_DATA_DIR", "./mcp-data"),
            namespace=os.getenv("SOCIAL_FETCH_NS", "research"),
        )
    return _client


def resource(url: str) -> dict:
    try:
        result = _library().resource(url)
    except Exception as exc:
        return {"error": "request_failed", "detail": f"{type(exc).__name__}: {exc}"}
    return result if isinstance(result, dict) else {"result": result}


def download(url: str, wait: bool = False) -> dict:
    try:
        result = _library().download(url, wait=wait)
    except Exception as exc:
        return request_failed(f"{type(exc).__name__}: {exc}")
    return result if isinstance(result, dict) else {"result": result}


def account(url: str, count: int = 3) -> dict:
    try:
        result = _library().account(url, count=count)
    except Exception as exc:
        return request_failed(f"{type(exc).__name__}: {exc}")
    return result if isinstance(result, dict) else {"result": result}


def download_image(url: str) -> dict:
    try:
        result = _library().download_image(url)
    except Exception as exc:
        return request_failed(f"{type(exc).__name__}: {exc}")
    return result if isinstance(result, dict) else {"result": result}


def as_envelope(data: dict, source_name: str, errors: list | None = None) -> dict:
    return envelope(data, source_name, errors)
