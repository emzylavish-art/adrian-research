"""Universal tool behavior. Called from tools appended to server.py."""
from __future__ import annotations

import os
import re
from pathlib import Path
from urllib.parse import quote, urlparse

from research_mcp.util.api import SOCIALFETCH_BASE, api_get, socialfetch_key
from research_mcp.util.easydown import easydown_parse
from research_mcp.util.errors import (
    bad_request,
    not_found,
    request_failed,
    unsupported_content,
    unsupported_platform,
)
from research_mcp.util.limits import clamp_count, default_timeout
from research_mcp.util.platform_owners import (
    SOCIAL_FETCH_COMMENTS,
    SOCIAL_FETCH_SEARCH,
    metadata_backends,
    profile_url,
)
from research_mcp.util.schema import normalize
from research_mcp.util.urls import canonicalize

_client_cache = None
_CUE = re.compile(r"^\d+$")


def _client():
    global _client_cache
    if _client_cache is None:
        from social_fetch import Client

        _client_cache = Client(
            data_dir=os.getenv("SOCIAL_FETCH_DATA_DIR", "./mcp-data"),
            namespace=os.getenv("SOCIAL_FETCH_NS", "research"),
        )
    return _client_cache


def _library(fn, *args, **kwargs) -> dict:
    try:
        result = fn(*args, **kwargs)
    except TimeoutError as exc:
        return {"error": "relay_timeout", "detail": str(exc), "retry": True}
    except FileNotFoundError as exc:
        return {"error": "not_found", "detail": str(exc)}
    except ValueError as exc:
        return {"error": "bad_request", "detail": str(exc)}
    except RuntimeError as exc:
        return {"error": "upstream_error", "detail": str(exc), "retry": True}
    except Exception as exc:
        return {"error": "request_failed", "detail": f"{type(exc).__name__}: {exc}"}
    return result if isinstance(result, dict) else {"result": result}


def _is_error(payload: dict) -> bool:
    return isinstance(payload, dict) and "error" in payload and "data" not in payload


def _credits(payload: dict) -> int:
    meta = payload.get("meta") if isinstance(payload, dict) else None
    if isinstance(meta, dict) and isinstance(meta.get("creditsCharged"), int):
        return meta["creditsCharged"]
    return 0


def _page(payload: dict) -> tuple[str | None, bool]:
    data = payload.get("data") if isinstance(payload, dict) else None
    page = data.get("page") if isinstance(data, dict) else None
    if not isinstance(page, dict):
        return None, False
    return page.get("nextCursor"), bool(page.get("hasMore"))


def _rows(payload: dict) -> list:
    data = payload.get("data") if isinstance(payload, dict) else None
    if isinstance(data, list):
        return data
    if not isinstance(data, dict):
        return []
    for key in ("videos", "products", "suggestions", "users", "comments", "replies", "items", "results"):
        if isinstance(data.get(key), list):
            return data[key]
    if isinstance(data.get("posts"), list):
        return data["posts"]
    return []


def strip_timing_cues(content: str) -> str:
    lines = []
    for line in content.splitlines():
        stripped = line.strip()
        if not stripped or stripped.upper() == "WEBVTT" or stripped.startswith("NOTE"):
            continue
        if "-->" in stripped or _CUE.match(stripped):
            continue
        lines.append(stripped)
    return "\n".join(lines)


def _guard(text: str, name: str) -> str | dict:
    if not isinstance(text, str) or not text.strip():
        return bad_request(f"{name} is required")
    return text.strip()


def _map_tiktok_video(payload: dict) -> dict:
    data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
    video = data.get("video") if isinstance(data.get("video"), dict) else {}
    author = data.get("author") if isinstance(data.get("author"), dict) else {}
    metrics = data.get("metrics") if isinstance(data.get("metrics"), dict) else {}
    media = data.get("media") if isinstance(data.get("media"), dict) else {}
    music = data.get("music") if isinstance(data.get("music"), dict) else None
    status = data.get("lookupStatus")
    errors = []
    if status and status != "found":
        errors.append(not_found(str(status)))
    dimensions = media.get("dimensions") if isinstance(media.get("dimensions"), dict) else {}
    video_urls = [item for item in (media.get("downloadWithoutWatermarkUrl"), media.get("downloadUrl")) if item]
    handle = author.get("handle")
    return {
        "content_type": "image" if video.get("mediaType") == "slideshow" else "video",
        "title": video.get("caption"),
        "description": video.get("caption"),
        "canonical_url": video.get("url"),
        "author": {
            "username": handle,
            "display_name": author.get("nickname"),
            "bio": author.get("signature"),
            "verified": author.get("verified"),
            "avatar_url": author.get("avatarUrl"),
            "profile_url": f"https://www.tiktok.com/@{handle}" if handle else None,
        },
        "created_at": video.get("createdAt"),
        "metrics": {
            "views": metrics.get("views"),
            "likes": metrics.get("likes"),
            "comments": metrics.get("comments"),
            "shares": metrics.get("shares"),
            "saves": metrics.get("saves"),
        },
        "media": {
            "thumbnail_url": media.get("thumbnailUrl"),
            "video_urls": video_urls,
            "image_urls": list(media.get("slideshowImages") or []),
            "duration_ms": video.get("durationMs"),
            "width": dimensions.get("width"),
            "height": dimensions.get("height"),
        },
        "transcript": data.get("transcript"),
        "is_ad": video.get("isAd"),
        "music": None if not music else {
            "title": music.get("title"),
            "artist": music.get("author"),
            "url": music.get("playUrl"),
        },
        "credits_charged": _credits(payload),
        "errors": errors,
        "raw_platform_data": payload,
    }


def _map_tiktok_profile(payload: dict, handle: str, platform: str = "tiktok") -> dict:
    data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
    profile = data.get("profile") if isinstance(data.get("profile"), dict) else {}
    metrics = data.get("metrics") if isinstance(data.get("metrics"), dict) else {}
    status = data.get("lookupStatus")
    errors = [not_found(str(status))] if status and status != "found" else []
    fallback = profile_url(platform, handle)
    return {
        "content_type": "text",
        "title": profile.get("displayName") or handle,
        "description": profile.get("bio"),
        "author": {
            "username": profile.get("handle") or handle,
            "display_name": profile.get("displayName"),
            "bio": profile.get("bio"),
            "followers": metrics.get("followers"),
            "verified": profile.get("verified"),
            "avatar_url": profile.get("avatarUrl"),
            "profile_url": profile.get("profileUrl") or fallback,
        },
        "metrics": {"likes": metrics.get("likes")},
        "credits_charged": _credits(payload),
        "errors": errors,
        "raw_platform_data": payload,
    }


def _map_easydown(payload: dict) -> dict:
    if _is_error(payload):
        return {"errors": [payload], "raw_platform_data": payload}
    data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
    media = data.get("media") if isinstance(data.get("media"), dict) else data
    if payload.get("status") not in (None, 200) or not media:
        code = payload.get("code") or "request_failed"
        mapped = not_found(payload.get("msg")) if code in {"content_unavailable", "no_media"} else {
            "error": code,
            "detail": payload.get("msg"),
        }
        return {"errors": [mapped], "raw_platform_data": payload}
    images = [item.get("url") for item in media.get("images") or [] if isinstance(item, dict) and item.get("url")]
    videos = [item.get("url") for item in media.get("videos") or [] if isinstance(item, dict) and item.get("url")]
    audios = [item.get("url") for item in media.get("audios") or [] if isinstance(item, dict) and item.get("url")]
    first_video = next((item for item in media.get("videos") or [] if isinstance(item, dict)), {})
    duration = media.get("duration")
    duration_ms = int(duration * 1000) if isinstance(duration, (int, float)) else None
    if videos:
        content_type = "video"
    elif images and audios:
        content_type = "mixed"
    elif images:
        content_type = "image"
    elif audios:
        content_type = "audio"
    else:
        content_type = None
    platform_data = data.get("platformData") if isinstance(data.get("platformData"), dict) else {}
    author = platform_data.get("author") if isinstance(platform_data.get("author"), dict) else {}
    statistics = platform_data.get("statistics") if isinstance(platform_data.get("statistics"), dict) else {}
    music = platform_data.get("music") if isinstance(platform_data.get("music"), dict) else None
    return {
        "content_type": content_type,
        "title": media.get("title") or platform_data.get("desc") or platform_data.get("title"),
        "description": platform_data.get("desc") or platform_data.get("abstract") or media.get("title"),
        "author": {
            "username": author.get("unique_id") or author.get("uniqueId"),
            "display_name": author.get("nickname") or author.get("name"),
            "avatar_url": author.get("avatar") or author.get("avatar_thumb"),
        },
        "metrics": {
            "views": statistics.get("play_count") or statistics.get("playCount"),
            "likes": statistics.get("digg_count") or statistics.get("diggCount"),
            "comments": statistics.get("comment_count") or statistics.get("commentCount"),
            "shares": statistics.get("share_count") or statistics.get("shareCount"),
        },
        "media": {
            "thumbnail_url": media.get("thumbnail"),
            "video_urls": videos,
            "image_urls": images,
            "audio_urls": audios,
            "duration_ms": duration_ms,
            "width": first_video.get("width"),
            "height": first_video.get("height"),
        },
        "music": None if not music else {
            "title": music.get("title"),
            "artist": music.get("author") or music.get("authorName"),
            "url": music.get("play_url") or music.get("playUrl"),
        },
        "raw_platform_data": payload,
        "errors": [],
    }


def _map_resource(payload: dict) -> dict:
    text = payload.get("text") or payload.get("readable_text") or payload.get("content")
    return {
        "content_type": "text" if text else None,
        "title": payload.get("title"),
        "description": text if isinstance(text, str) else None,
        "raw_platform_data": payload,
        "errors": [payload] if _is_error(payload) else [],
    }


def _lookup_tiktok_video(url: str, transcript: bool = False) -> dict:
    return api_get(
        SOCIALFETCH_BASE,
        "/v1/tiktok/videos",
        {"url": url, "getTranscript": transcript},
        key=socialfetch_key(),
        timeout=120 if transcript else default_timeout("metadata"),
    )


def _map_bluesky_post(payload: dict) -> dict:
    data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
    post = data.get("post") if isinstance(data.get("post"), dict) else {}
    author = data.get("author") if isinstance(data.get("author"), dict) else {}
    metrics = data.get("metrics") if isinstance(data.get("metrics"), dict) else {}
    embed = data.get("embed") if isinstance(data.get("embed"), dict) else {}
    video = embed.get("video") if isinstance(embed.get("video"), dict) else {}
    images = [item.get("url") for item in embed.get("images") or [] if isinstance(item, dict) and item.get("url")]
    status = data.get("lookupStatus")
    errors = [not_found(str(status))] if status and status != "found" else []
    handle = author.get("handle")
    kind = embed.get("kind")
    content_type = {"video": "video", "images": "image", "external": "text"}.get(kind)
    return {
        "content_type": content_type,
        "title": post.get("text"),
        "description": post.get("text"),
        "canonical_url": post.get("url"),
        "created_at": post.get("createdAt"),
        "author": {
            "username": handle,
            "display_name": author.get("displayName"),
            "verified": author.get("verified"),
            "avatar_url": author.get("avatarUrl"),
            "profile_url": f"https://bsky.app/profile/{handle}" if handle else None,
        },
        "metrics": {
            "likes": metrics.get("likes"),
            "comments": metrics.get("replies"),
            "reposts": metrics.get("reposts"),
        },
        "media": {
            "thumbnail_url": video.get("thumbnailUrl"),
            "video_urls": [video["url"]] if video.get("url") else [],
            "image_urls": images,
        },
        "comments_preview": list(data.get("replies") or [])[:5],
        "credits_charged": _credits(payload),
        "errors": errors,
        "raw_platform_data": payload,
    }


def _fill(url: str, platform: str) -> tuple[dict, list, int]:
    errors = []
    credits = 0
    partial = {}
    for backend in metadata_backends(platform):
        if backend == "socialfetch_rest":
            if platform == "bluesky":
                payload = api_get(SOCIALFETCH_BASE, "/v1/bluesky/posts", {"url": url}, key=socialfetch_key())
                mapper = _map_bluesky_post
            else:
                payload = _lookup_tiktok_video(url)
                mapper = _map_tiktok_video
            if _is_error(payload):
                errors.append(payload)
                continue
            partial = mapper(payload)
            credits += partial.get("credits_charged") or 0
            return partial, errors + list(partial.get("errors") or []), credits
        if backend == "easydown":
            payload = easydown_parse(url, platform)
            if _is_error(payload):
                errors.append(payload)
                continue
            partial = _map_easydown(payload)
            if partial.get("errors") and not partial.get("title") and not (partial.get("media") or {}).get("video_urls"):
                errors.extend(partial["errors"])
                continue
            return partial, errors + list(partial.get("errors") or []), credits
        if backend == "social_fetch":
            payload = _library(_client().resource, url)
            partial = _map_resource(payload)
            return partial, errors + list(partial.get("errors") or []), credits
    return partial, errors, credits


def get_post(url: str, include_transcript: bool = False, include_comments: bool = False, download_media: bool = False) -> dict:
    checked = _guard(url, "url")
    if isinstance(checked, dict):
        return normalize({}, None, "", "", errors=[checked])
    canonical, platform = canonicalize(checked)
    if platform is None:
        host = urlparse(checked).netloc or checked
        return normalize({}, None, checked, canonical, errors=[unsupported_platform(host)])
    try:
        partial, errors, credits = _fill(canonical, platform)
    except Exception as exc:
        return normalize({}, platform, checked, canonical, errors=[request_failed(f"{type(exc).__name__}: {exc}")])
    if include_transcript and platform == "tiktok":
        transcript = get_transcript(canonical, use_ai_fallback=False)
        if transcript.get("transcript"):
            partial["transcript"] = transcript["transcript"]
        errors.extend(transcript.get("errors") or [])
        credits += transcript.get("credits_charged") or 0
    elif include_transcript:
        errors.append(unsupported_content("transcript lookup is TikTok-only today"))
    if include_comments:
        comments = get_comments(canonical, count=5)
        partial["comments_preview"] = (comments.get("comments") or [])[:5]
        errors.extend(comments.get("errors") or [])
        credits += comments.get("credits_charged") or 0
    if download_media:
        job = download_media_job(canonical, wait=True, timeout=default_timeout("download"))
        raw = partial.get("raw_platform_data")
        if not isinstance(raw, dict):
            raw = {"lookup": raw} if raw is not None else {}
        raw["local_download"] = job
        partial["raw_platform_data"] = raw
        if job.get("error"):
            errors.append(job)
    partial["credits_charged"] = credits
    partial["errors"] = errors
    if platform == "youtube" and not os.getenv("EASYDOWN_API_KEY"):
        # FREE-FIRST: EasyDown is the paid YouTube metadata path. A missing
        # key must not leave likes and dislikes null when the verified
        # returnyoutubedislike counts source can fill them. Other fields
        # stay null. This does not invent title, views, or media.
        partial, errors = _merge_youtube_counts(canonical, partial, errors)
        partial["errors"] = errors
    return normalize(partial, platform, checked, canonical)


def _merge_youtube_counts(url: str, partial: dict, errors: list) -> tuple[dict, list]:
    from research_mcp.backends.youtube_free import get_counts, get_metadata

    metadata = get_metadata(url)
    metadata_data = metadata.get("data") if isinstance(metadata.get("data"), dict) else {}
    if partial.get("title") is None and isinstance(metadata_data.get("title"), str):
        partial["title"] = metadata_data["title"]
    author = partial.get("author") if isinstance(partial.get("author"), dict) else {}
    if author.get("username") is None and isinstance(metadata_data.get("author"), str):
        author["username"] = metadata_data["author"]
        author["display_name"] = metadata_data["author"]
    if author.get("profile_url") is None and isinstance(metadata_data.get("author_url"), str):
        author["profile_url"] = metadata_data["author_url"]
    partial["author"] = author
    metrics = partial.get("metrics") if isinstance(partial.get("metrics"), dict) else {}
    if metrics.get("views") is None and isinstance(metadata_data.get("view_count"), int):
        metrics["views"] = metadata_data["view_count"]
    partial["metrics"] = metrics
    errors.extend(metadata.get("errors") or [])
    counted = get_counts(url)
    data = counted.get("data") if isinstance(counted.get("data"), dict) else {}
    if metrics.get("likes") is None and isinstance(data.get("likes"), int):
        metrics["likes"] = data["likes"]
    if isinstance(data.get("dislikes"), int):
        metrics["dislikes"] = data["dislikes"]
    partial["metrics"] = metrics
    partial["path_used"] = "free"
    library_filled = bool(partial.get("title") or (partial.get("media") or {}).get("video_urls"))
    partial["source_detail"] = "youtube-oembed-page+returnyoutubedislike"
    if not isinstance(partial.get("credits_charged"), int):
        partial["credits_charged"] = 0
    errors.extend(counted.get("errors") or [])
    if not library_filled and not partial.get("title") and not author.get("username") and metrics.get("views") is None:
        errors.append({
            "error": "missing_field",
            "detail": "free YouTube sources returned counts only; title, author, views, and media were not available",
        })
    return partial, errors


def search_posts(query: str, platform: str | None = None, count: int = 10, search=None) -> list:
    checked = _guard(query, "query")
    capped = clamp_count(count, default=10, hi=20)
    if isinstance(checked, dict):
        return [normalize({}, platform, "", "", errors=[checked])]
    if platform and platform not in SOCIAL_FETCH_SEARCH:
        return [normalize({}, platform, "", "", errors=[unsupported_platform(platform)])]
    sources = [platform] if platform else sorted(SOCIAL_FETCH_SEARCH)
    if search is None:
        from social_fetch.web_search import FootageSearch

        search = FootageSearch.from_env(include_catalogs=False)
    rows = []
    for source in sources:
        try:
            result = search.search(checked, source=source, count=capped)
        except Exception as exc:
            rows.append(normalize({}, source, "", "", errors=[request_failed(str(exc))]))
            continue
        for item in (result.get("results") or []) if isinstance(result, dict) else []:
            item_url = item.get("url") or ""
            canonical, detected = canonicalize(item_url) if item_url else ("", source)
            rows.append(normalize({
                "title": item.get("title"),
                "description": item.get("description"),
                "content_type": "video",
                "raw_platform_data": item,
            }, detected or source, item_url, canonical))
            if len(rows) >= capped:
                return rows[:capped]
    return rows[:capped]


def get_profile(handle: str, platform: str) -> dict:
    checked = _guard(handle, "handle")
    if isinstance(checked, dict):
        return normalize({}, platform, "", "", errors=[checked])
    if not isinstance(platform, str) or not platform.strip():
        return normalize({}, None, "", "", errors=[bad_request("platform is required")])
    platform = platform.strip().lower()
    name = checked.lstrip("@")
    if platform in {"tiktok", "bluesky"}:
        path = "/v1/bluesky/profiles/{handle}" if platform == "bluesky" else "/v1/tiktok/profiles/{handle}"
        payload = api_get(
            SOCIALFETCH_BASE,
            path.format(handle=quote(name, safe="")),
            key=socialfetch_key(),
        )
        if _is_error(payload):
            return normalize({}, platform, profile_url(platform, name) or "", profile_url(platform, name) or "", errors=[payload])
        partial = _map_tiktok_profile(payload, name, platform)
        return normalize(partial, platform, partial["author"]["profile_url"], partial["author"]["profile_url"])
    url = profile_url(platform, name)
    if url and platform in SOCIAL_FETCH_SEARCH:
        sample = _library(_client().account, url, count=3)
        errors = [sample] if _is_error(sample) else []
        errors.append(unsupported_content("full profile fields are not exposed for this platform; returning the library account sample"))
        return normalize({"raw_platform_data": sample, "author": {"username": name, "profile_url": url}, "errors": errors}, platform, url, url)
    return normalize({}, platform, url or "", url or "", errors=[unsupported_platform(platform)])


def list_profile_posts(handle: str, platform: str, count: int = 20, cursor: str | None = None) -> dict:
    checked = _guard(handle, "handle")
    if isinstance(checked, dict):
        return {"posts": [], "cursor": None, "has_more": False, "errors": [checked]}
    if not isinstance(platform, str) or not platform.strip():
        return {"posts": [], "cursor": None, "has_more": False, "errors": [bad_request("platform is required")]}
    platform = platform.strip().lower()
    capped = clamp_count(count, default=20)
    name = checked.lstrip("@")
    if platform in {"tiktok", "bluesky"}:
        path = "/v1/bluesky/profiles/{handle}/posts" if platform == "bluesky" else "/v1/tiktok/profiles/{handle}/videos"
        payload = api_get(
            SOCIALFETCH_BASE,
            path.format(handle=quote(name, safe="")),
            {"cursor": cursor},
            key=socialfetch_key(),
        )
        if _is_error(payload):
            return {"posts": [], "cursor": None, "has_more": False, "errors": [payload]}
        next_cursor, has_more = _page(payload)
        posts = []
        for item in _rows(payload)[:capped]:
            url = item.get("url") if isinstance(item, dict) else None
            title = None if not isinstance(item, dict) else item.get("caption") or item.get("text")
            posts.append(normalize({"title": title, "raw_platform_data": item}, platform, url or "", url or ""))
        if len(_rows(payload)) > capped:
            has_more = True
        return {"posts": posts, "cursor": next_cursor, "has_more": has_more, "errors": [], "credits_charged": _credits(payload)}
    url = profile_url(platform, name)
    if not url or platform not in SOCIAL_FETCH_SEARCH:
        return {"posts": [], "cursor": None, "has_more": False, "errors": [unsupported_platform(platform)]}
    sample = _library(_client().account, url, count=capped)
    return {
        "posts": [],
        "cursor": None,
        "has_more": False,
        "errors": [unsupported_content("paginated profile posts are not exposed for this platform")],
        "raw_platform_data": sample,
    }


def get_transcript(url: str, use_ai_fallback: bool = False, language: str | None = None) -> dict:
    checked = _guard(url, "url")
    if isinstance(checked, dict):
        return normalize({}, None, "", "", errors=[checked])
    canonical, platform = canonicalize(checked)
    if platform != "tiktok":
        errors = [unsupported_content("AI fallback is TikTok-only today" if use_ai_fallback else "transcript lookup is TikTok-only today")]
        return normalize({"transcript": None, "errors": errors}, platform, checked, canonical)
    if language and not re.fullmatch(r"[A-Za-z]{2}", language.strip()):
        return normalize({}, platform, checked, canonical, errors=[bad_request("language must be an ISO 639-1 code")])
    payload = api_get(
        SOCIALFETCH_BASE,
        "/v1/tiktok/videos/transcript",
        {
            "url": canonical,
            "useAiFallback": use_ai_fallback,
            "language": None if not language else language.strip().lower(),
        },
        key=socialfetch_key(),
    )
    if _is_error(payload):
        return normalize({}, platform, checked, canonical, errors=[payload])
    data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
    transcript = data.get("transcript") if isinstance(data.get("transcript"), dict) else None
    if transcript and isinstance(transcript.get("content"), str):
        transcript = dict(transcript)
        transcript["text"] = strip_timing_cues(transcript["content"])
    errors = []
    if data.get("lookupStatus") and data.get("lookupStatus") != "found":
        errors.append(not_found(str(data.get("lookupStatus"))))
    return normalize({
        "transcript": transcript,
        "credits_charged": _credits(payload),
        "raw_platform_data": payload,
        "errors": errors,
    }, platform, checked, canonical)


def get_comments(url: str, count: int = 20, cursor: str | None = None) -> dict:
    checked = _guard(url, "url")
    if isinstance(checked, dict):
        return {"comments": [], "comments_preview": [], "cursor": None, "has_more": False, "errors": [checked]}
    canonical, platform = canonicalize(checked)
    capped = clamp_count(count, default=20)
    if platform == "bluesky":
        payload = api_get(SOCIALFETCH_BASE, "/v1/bluesky/posts", {"url": canonical}, key=socialfetch_key())
        if _is_error(payload):
            return {"comments": [], "comments_preview": [], "cursor": None, "has_more": False, "errors": [payload], "platform": platform, "url": checked}
        data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
        comments = list(data.get("replies") or [])[:capped]
        return {
            "comments": comments,
            "comments_preview": comments[:5],
            "cursor": None,
            "has_more": False,
            "errors": [],
            "platform": platform,
            "url": checked,
            "canonical_url": canonical,
            "credits_charged": _credits(payload),
            "raw_platform_data": payload,
        }
    if platform == "tiktok":
        payload = api_get(
            SOCIALFETCH_BASE,
            "/v1/tiktok/videos/comments",
            {"url": canonical, "cursor": cursor},
            key=socialfetch_key(),
        )
        if _is_error(payload):
            return {"comments": [], "comments_preview": [], "cursor": None, "has_more": False, "errors": [payload], "platform": platform, "url": checked}
        next_cursor, has_more = _page(payload)
        comments = _rows(payload)[:capped]
        return {
            "comments": comments,
            "comments_preview": comments[:5],
            "cursor": next_cursor,
            "has_more": has_more or len(_rows(payload)) > capped,
            "errors": [],
            "platform": platform,
            "url": checked,
            "canonical_url": canonical,
            "credits_charged": _credits(payload),
            "raw_platform_data": payload,
        }
    if platform in SOCIAL_FETCH_COMMENTS:
        payload = _library(_client().comments, canonical, count=capped)
        comments = payload if isinstance(payload, list) else payload.get("comments") or payload.get("result") or []
        if not isinstance(comments, list):
            comments = []
        errors = [payload] if isinstance(payload, dict) and _is_error(payload) else []
        return {
            "comments": comments[:capped],
            "comments_preview": comments[:5],
            "cursor": None,
            "has_more": False,
            "errors": errors,
            "platform": platform,
            "url": checked,
            "canonical_url": canonical,
        }
    return {
        "comments": [],
        "comments_preview": [],
        "cursor": None,
        "has_more": False,
        "errors": [unsupported_content("comments are not exposed for that platform")],
        "platform": platform,
        "url": checked,
        "canonical_url": canonical,
    }


def get_comment_replies(comment_id: str, count: int = 20, cursor: str | None = None, url: str | None = None) -> dict:
    checked = _guard(comment_id, "comment_id")
    if isinstance(checked, dict):
        return {"comments": [], "errors": [checked]}
    if not isinstance(url, str) or not url.strip():
        return {"comments": [], "errors": [bad_request("url is required for TikTok reply lookup")]}
    canonical, platform = canonicalize(url.strip())
    if platform != "tiktok":
        return {"comments": [], "errors": [unsupported_content("comment replies are TikTok-only today")], "platform": platform}
    payload = api_get(
        SOCIALFETCH_BASE,
        "/v1/tiktok/videos/comments/replies",
        {"commentId": checked, "url": canonical, "cursor": cursor},
        key=socialfetch_key(),
    )
    if _is_error(payload):
        return {"comments": [], "errors": [payload], "platform": platform}
    comments = _rows(payload)[:clamp_count(count, default=20)]
    next_cursor, has_more = _page(payload)
    return {
        "comments": comments,
        "comments_preview": comments[:5],
        "cursor": next_cursor,
        "has_more": has_more,
        "errors": [],
        "platform": platform,
        "url": url,
        "canonical_url": canonical,
        "credits_charged": _credits(payload),
    }


def get_trending(platform: str | None = None, region: str | None = None, count: int = 20) -> dict:
    chosen = (platform or "").strip().lower()
    if chosen != "tiktok":
        return normalize({}, chosen or None, "", "", errors=[{
            "error": "unsupported_platform",
            "detail": "trending is TikTok-only; pass platform='tiktok'",
        }])
    region_value = (region or os.getenv("SOCIALFETCH_REGION") or "US").strip().upper()
    if len(region_value) != 2 or not region_value.isalpha():
        return normalize({}, "tiktok", "", "", errors=[bad_request("region must be a two-letter country code")])
    payload = api_get(
        SOCIALFETCH_BASE,
        "/v1/tiktok/feed/trending",
        {"region": region_value},
        key=socialfetch_key(),
    )
    if _is_error(payload):
        return normalize({}, "tiktok", "", "", errors=[payload])
    posts = []
    for item in _rows(payload)[:clamp_count(count, default=20)]:
        item_url = item.get("url") if isinstance(item, dict) else ""
        posts.append(normalize({"raw_platform_data": item, "title": item.get("caption") if isinstance(item, dict) else None}, "tiktok", item_url or "", item_url or ""))
    return normalize({
        "content_type": "video",
        "title": f"TikTok trending {region_value}",
        "raw_platform_data": {"posts": posts, "upstream": payload},
        "credits_charged": _credits(payload),
    }, "tiktok", "https://www.tiktok.com/", "https://www.tiktok.com/")


def download_media_job(url: str, output_dir: str | None = None, wait: bool = True, timeout: int = 900) -> dict:
    checked = _guard(url, "url")
    if isinstance(checked, dict):
        return checked
    canonical, platform = canonicalize(checked)
    if platform is None:
        return unsupported_platform(urlparse(checked).netloc or checked)
    job = _library(_client().download, canonical, wait=wait, timeout=timeout)
    if job.get("error") or not wait or job.get("status") != "ready":
        if output_dir and not job.get("error") and job.get("status") != "ready":
            job = dict(job)
            job["export"] = "not_ready"
        return job
    if "id" not in job:
        return {**job, "error": "request_failed", "detail": "download did not return a job id"}
    destination = Path(output_dir or os.getenv("SOCIAL_FETCH_DATA_DIR", "./mcp-data") + "/downloads").expanduser()
    try:
        destination.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        return {**job, "error": "bad_request", "detail": str(exc)}
    out = destination / f"{job['id']}.mp4"
    if out.exists():
        return {**job, "exported_to": str(out), "export": "already_present"}
    exported = _library(_client().export, job["id"], out)
    return exported


def export_media(job_id: str, output_path: str) -> dict:
    job = _guard(job_id, "job_id")
    path = _guard(output_path, "output_path")
    if isinstance(job, dict):
        return job
    if isinstance(path, dict):
        return path
    return _library(_client().export, job, path)


def media_status(job_id: str) -> dict:
    job = _guard(job_id, "job_id")
    if isinstance(job, dict):
        return job
    return _library(_client().status, job)


def fetch_resource(url: str) -> dict:
    checked = _guard(url, "url")
    if isinstance(checked, dict):
        return normalize({}, None, "", "", errors=[checked])
    canonical, platform = canonicalize(checked)
    payload = _library(_client().resource, canonical)
    partial = _map_resource(payload)
    return normalize(partial, platform, checked, canonical)


def search_hashtags(query: str, count: int = 10) -> dict:
    checked = _guard(query, "query")
    if isinstance(checked, dict):
        return {"results": [], "errors": [checked], "platform": "tiktok"}
    payload = api_get(
        SOCIALFETCH_BASE,
        "/v1/tiktok/search/hashtags",
        {"hashtag": checked.lstrip("#")},
        key=socialfetch_key(),
    )
    if _is_error(payload):
        return {"results": [], "errors": [payload], "platform": "tiktok"}
    results = []
    for item in _rows(payload)[:clamp_count(count)]:
        item_url = item.get("url") if isinstance(item, dict) else ""
        results.append(normalize({"raw_platform_data": item}, "tiktok", item_url or "", item_url or ""))
    return {"results": results, "errors": [], "platform": "tiktok", "credits_charged": _credits(payload), "raw_platform_data": payload}


def search_suggestions(query: str) -> dict:
    checked = _guard(query, "query")
    if isinstance(checked, dict):
        return {"suggestions": [], "errors": [checked], "platform": "tiktok"}
    payload = api_get(SOCIALFETCH_BASE, "/v1/tiktok/search/suggestions", {"query": checked}, key=socialfetch_key())
    if _is_error(payload):
        return {"suggestions": [], "errors": [payload], "platform": "tiktok"}
    return {
        "suggestions": _rows(payload),
        "errors": [],
        "platform": "tiktok",
        "credits_charged": _credits(payload),
        "raw_platform_data": payload,
    }


def search_shop_products(query: str, count: int = 10) -> dict:
    checked = _guard(query, "query")
    if isinstance(checked, dict):
        return {"results": [], "errors": [checked], "platform": "tiktok"}
    payload = api_get(
        SOCIALFETCH_BASE,
        "/v1/tiktok/shop/products/search",
        {"query": checked},
        key=socialfetch_key(),
    )
    if _is_error(payload):
        return {"results": [], "errors": [payload], "platform": "tiktok"}
    return {
        "results": _rows(payload)[:clamp_count(count)],
        "errors": [],
        "platform": "tiktok",
        "credits_charged": _credits(payload),
        "raw_platform_data": payload,
    }


def get_account_sample(url: str, count: int = 3) -> dict:
    checked = _guard(url, "url")
    if isinstance(checked, dict):
        return {"sample": None, "errors": [checked]}
    canonical, platform = canonicalize(checked)
    sample = _library(_client().account, canonical, count=clamp_count(count, default=3))
    errors = [sample] if isinstance(sample, dict) and _is_error(sample) else []
    return {"sample": sample, "errors": errors, "platform": platform, "url": checked, "canonical_url": canonical}
