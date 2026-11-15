"""Typed error dicts. Tools return these. They do not raise into the MCP session."""


def relay_timeout(detail: str) -> dict:
    return {"error": "relay_timeout", "detail": detail, "retry": True}


def auth_failed(detail: str = "check API key") -> dict:
    return {"error": "auth_failed", "detail": detail}


def not_found(detail: str | None = None) -> dict:
    out = {"error": "not_found"}
    if detail:
        out["detail"] = detail
    return out


def rate_limited(retry_after: int | str | None = None) -> dict:
    return {"error": "rate_limited", "retry_after": retry_after}


def upstream_error(status: int, detail: str | None = None) -> dict:
    out = {"error": "upstream_error", "status": status, "retry": True}
    if detail:
        out["detail"] = detail
    return out


def unsupported_platform(domain: str) -> dict:
    return {"error": "unsupported_platform", "detail": f"no resolver for domain {domain}"}


def unsupported_content(detail: str) -> dict:
    return {"error": "unsupported_content", "detail": detail}


def api_key_missing(base: str) -> dict:
    return {"error": "api_key_missing", "detail": f"no key configured for {base}"}


def request_failed(detail: str) -> dict:
    return {"error": "request_failed", "detail": detail}


def bad_request(detail: str) -> dict:
    return {"error": "bad_request", "detail": detail}
