"""Next TikTok tools. Paths are the 2026-11-15 Social Fetch catalog, not guesses.

These calls are TikTok-only. They do not replace search_videos.
credits_charged is copied from meta.creditsCharged. Catalog prices in the
docstrings are warnings, not values written into the result.
"""
from __future__ import annotations

import re
from urllib.parse import quote

from research_mcp.util.api import SOCIALFETCH_BASE, api_get, socialfetch_key
from research_mcp.util.errors import bad_request, not_found

DATE_POSTED = {"yesterday", "this-week", "this-month", "last-3-months", "last-6-months", "all-time"}
SEARCH_SORT = {"relevance", "most-liked", "date-posted"}
SHOP_REGION = {"US", "GB", "DE", "FR", "IT", "ID", "MY", "MX", "PH", "SG", "ES", "TH", "VN", "BR", "JP", "IE"}
SHOP_SORT = {"top", "new-releases"}
AD_COUNTRY = {
    "ALL", "AT", "BE", "BG", "BR", "CH", "CY", "CZ", "DE", "DK", "EE", "ES", "FI", "FR",
    "GB", "GR", "HR", "HU", "IE", "IS", "IT", "LI", "LT", "LU", "LV", "MT", "NL", "NO",
    "PL", "PT", "RO", "SE", "SI", "SK", "TR",
}
_LIST_KEYS = (
    "videos", "products", "suggestions", "users", "comments", "replies",
    "followers", "following", "ads", "reviews", "items", "results",
)
_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _blank(error: dict | None = None) -> dict:
    return {
        "platform": "tiktok",
        "results": [],
        "cursor": None,
        "has_more": False,
        "lookup_status": None,
        "credits_charged": 0,
        "errors": [] if error is None else [error],
        "raw_platform_data": None,
    }


def _guard(value, name: str) -> str | dict:
    if not isinstance(value, str) or not value.strip():
        return bad_request(f"{name} is required")
    return value.strip()


def _region(value: str | None, allowed: set[str] | None = None) -> str | dict | None:
    if value is None or value == "":
        return None
    if not isinstance(value, str):
        return bad_request("region must be a string")
    region = value.strip().upper()
    if allowed is not None:
        if region not in allowed:
            return bad_request(f"region must be one of {', '.join(sorted(allowed))}")
        return region
    if len(region) != 2 or not region.isalpha():
        return bad_request("region must be a two-letter country code")
    return region


def _choice(value: str | None, allowed: set[str], name: str) -> str | dict | None:
    if value is None or value == "":
        return None
    if not isinstance(value, str) or value.strip() not in allowed:
        return bad_request(f"{name} must be one of {', '.join(sorted(allowed))}")
    return value.strip()


def _rows(payload: dict) -> list:
    data = payload.get("data") if isinstance(payload, dict) else None
    if isinstance(data, list):
        return data
    if not isinstance(data, dict):
        return []
    for key in _LIST_KEYS:
        if isinstance(data.get(key), list):
            return data[key]
    return []


def _page(payload: dict) -> tuple[str | None, bool]:
    data = payload.get("data") if isinstance(payload, dict) else None
    page = data.get("page") if isinstance(data, dict) else None
    if not isinstance(page, dict):
        return None, False
    return page.get("nextCursor"), bool(page.get("hasMore"))


def _credits(payload: dict) -> int:
    meta = payload.get("meta") if isinstance(payload, dict) else None
    if isinstance(meta, dict) and isinstance(meta.get("creditsCharged"), int):
        return meta["creditsCharged"]
    return 0


def _confirm(confirm: bool, detail: str) -> dict | None:
    if confirm:
        return None
    return bad_request(detail)


def _call(path: str, params: dict | None = None, *, confirm: bool = True, cost: str | None = None) -> dict:
    held = None if confirm or not cost else _confirm(False, cost)
    if held:
        return _blank(held)
    payload = api_get(SOCIALFETCH_BASE, path, params or {}, key=socialfetch_key())
    if isinstance(payload, dict) and "error" in payload and "data" not in payload:
        return _blank(payload)
    data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
    status = data.get("lookupStatus")
    errors = []
    if status in {"not_found", "private", "hidden"}:
        errors.append(not_found(str(status)))
    cursor, has_more = _page(payload)
    return {
        "platform": "tiktok",
        "results": _rows(payload),
        "cursor": cursor,
        "has_more": has_more,
        "lookup_status": status,
        "credits_charged": _credits(payload),
        "errors": errors,
        "raw_platform_data": payload,
    }


def _handle_path(handle: str, suffix: str = "") -> str | dict:
    checked = _guard(handle, "handle")
    if isinstance(checked, dict):
        return checked
    return f"/v1/tiktok/profiles/{quote(checked.lstrip('@'), safe='')}{suffix}"


def search_tiktok_videos(query: str, date_posted: str | None = None, sort_by: str | None = None, region: str | None = None, cursor: str | None = None) -> dict:
    checked = _guard(query, "query")
    if isinstance(checked, dict):
        return _blank(checked)
    posted = _choice(date_posted, DATE_POSTED, "date_posted")
    sort = _choice(sort_by, SEARCH_SORT, "sort_by")
    country = _region(region)
    for item in (posted, sort, country):
        if isinstance(item, dict):
            return _blank(item)
    return _call("/v1/tiktok/search", {"query": checked, "datePosted": posted, "sortBy": sort, "region": country, "cursor": cursor})


def search_tiktok_top(query: str, date_posted: str | None = None, sort_by: str | None = None, region: str | None = None, cursor: str | None = None) -> dict:
    checked = _guard(query, "query")
    if isinstance(checked, dict):
        return _blank(checked)
    posted = _choice(date_posted, DATE_POSTED, "date_posted")
    sort = _choice(sort_by, SEARCH_SORT, "sort_by")
    country = _region(region)
    for item in (posted, sort, country):
        if isinstance(item, dict):
            return _blank(item)
    return _call("/v1/tiktok/search/top", {"query": checked, "datePosted": posted, "sortBy": sort, "region": country, "cursor": cursor})


def search_tiktok_users(query: str, cursor: str | None = None) -> dict:
    checked = _guard(query, "query")
    if isinstance(checked, dict):
        return _blank(checked)
    return _call("/v1/tiktok/users/search", {"query": checked, "cursor": cursor})


def list_tiktok_followers(handle: str, cursor: str | None = None, user_id: str | None = None) -> dict:
    path = _handle_path(handle, "/followers")
    if isinstance(path, dict):
        return _blank(path)
    return _call(path, {"cursor": cursor, "userId": user_id})


def list_tiktok_following(handle: str, cursor: str | None = None) -> dict:
    path = _handle_path(handle, "/following")
    if isinstance(path, dict):
        return _blank(path)
    return _call(path, {"cursor": cursor})


def get_tiktok_region(handle: str) -> dict:
    path = _handle_path(handle, "/region")
    if isinstance(path, dict):
        return _blank(path)
    return _call(path)


def get_tiktok_audience(handle: str, confirm: bool = False) -> dict:
    path = _handle_path(handle, "/audience")
    if isinstance(path, dict):
        return _blank(path)
    return _call(path, confirm=confirm, cost="TikTok audience lookup is catalogued at 30 credits; pass confirm=True")


def get_tiktok_engagement(handle: str, confirm: bool = False) -> dict:
    path = _handle_path(handle, "/engagement")
    if isinstance(path, dict):
        return _blank(path)
    return _call(path, confirm=confirm, cost="TikTok engagement lookup is catalogued at 5 credits; pass confirm=True")


def get_tiktok_live(handle: str) -> dict:
    path = _handle_path(handle, "/live")
    if isinstance(path, dict):
        return _blank(path)
    return _call(path)


def get_tiktok_live_info(room_id: str, user_id: str) -> dict:
    room = _guard(room_id, "room_id")
    user = _guard(user_id, "user_id")
    if isinstance(room, dict):
        return _blank(room)
    if isinstance(user, dict):
        return _blank(user)
    return _call("/v1/tiktok/live", {"roomId": room, "userId": user})


def get_tiktok_hosted_media(url: str, region: str | None = None, confirm: bool = False) -> dict:
    checked = _guard(url, "url")
    if isinstance(checked, dict):
        return _blank(checked)
    country = _region(region)
    if isinstance(country, dict):
        return _blank(country)
    return _call(
        "/v1/tiktok/videos/download",
        {"url": checked, "region": country},
        confirm=confirm,
        cost="hosted TikTok media is catalogued at 11 credits when a file is returned; pass confirm=True",
    )


def list_tiktok_collection(url: str, cursor: str | None = None) -> dict:
    checked = _guard(url, "url")
    if isinstance(checked, dict):
        return _blank(checked)
    return _call("/v1/tiktok/collections/videos", {"url": checked, "cursor": cursor})


def get_tiktok_song(song_id: str) -> dict:
    checked = _guard(song_id, "song_id")
    if isinstance(checked, dict):
        return _blank(checked)
    return _call("/v1/tiktok/songs", {"id": checked})


def list_tiktok_sound_videos(clip_id: str, cursor: str | None = None) -> dict:
    checked = _guard(clip_id, "clip_id")
    if isinstance(checked, dict):
        return _blank(checked)
    return _call(f"/v1/tiktok/music/{quote(checked, safe='')}/videos", {"cursor": cursor})


def list_tiktok_store_products(url: str, cursor: str | None = None, region: str | None = None, sort_by: str | None = None) -> dict:
    checked = _guard(url, "url")
    if isinstance(checked, dict):
        return _blank(checked)
    country = _region(region, SHOP_REGION)
    sort = _choice(sort_by, SHOP_SORT, "sort_by")
    for item in (country, sort):
        if isinstance(item, dict):
            return _blank(item)
    return _call("/v1/tiktok/shop/products", {"url": checked, "cursor": cursor, "region": country, "sortBy": sort})


def get_tiktok_product(url: str, region: str | None = None) -> dict:
    checked = _guard(url, "url")
    if isinstance(checked, dict):
        return _blank(checked)
    country = _region(region, SHOP_REGION)
    if isinstance(country, dict):
        return _blank(country)
    return _call("/v1/tiktok/products", {"url": checked, "region": country})


def list_tiktok_product_reviews(url: str | None = None, product_id: str | None = None, region: str | None = None, page: int | None = None) -> dict:
    if not (isinstance(url, str) and url.strip()) and not (isinstance(product_id, str) and product_id.strip()):
        return _blank(bad_request("url or product_id is required"))
    country = _region(region, SHOP_REGION)
    if isinstance(country, dict):
        return _blank(country)
    page_value = None
    if page is not None:
        try:
            page_value = int(page)
        except (TypeError, ValueError):
            return _blank(bad_request("page must be an integer"))
        if page_value < 1:
            return _blank(bad_request("page must be 1 or greater"))
    return _call("/v1/tiktok/products/reviews", {
        "url": None if not isinstance(url, str) else url.strip() or None,
        "productId": None if not isinstance(product_id, str) else product_id.strip() or None,
        "region": country,
        "page": page_value,
    })


def list_tiktok_showcase(handle: str, cursor: str | None = None, region: str | None = None) -> dict:
    path = _handle_path(handle, "/showcase-products")
    if isinstance(path, dict):
        return _blank(path)
    country = _region(region)
    if isinstance(country, dict):
        return _blank(country)
    return _call(path, {"cursor": cursor, "region": country})


def get_tiktok_ad(ad_id: str | None = None, url: str | None = None) -> dict:
    if not (isinstance(ad_id, str) and ad_id.strip()) and not (isinstance(url, str) and url.strip()):
        return _blank(bad_request("ad_id or url is required"))
    return _call("/v1/tiktok/ad-library/ads", {
        "adId": None if not isinstance(ad_id, str) else ad_id.strip() or None,
        "url": None if not isinstance(url, str) else url.strip() or None,
    })


def search_tiktok_ads(
    query: str | None = None,
    advertiser_name: str | None = None,
    advertiser_business_id: str | None = None,
    country: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    cursor: str | None = None,
) -> dict:
    text = query.strip() if isinstance(query, str) else ""
    name = advertiser_name.strip() if isinstance(advertiser_name, str) else ""
    business = advertiser_business_id.strip() if isinstance(advertiser_business_id, str) else ""
    if not text and not name:
        return _blank(bad_request("query or advertiser_name is required"))
    if business and not name:
        return _blank(bad_request("advertiser_business_id requires advertiser_name"))
    if business and not re.fullmatch(r"\d{1,32}", business):
        return _blank(bad_request("advertiser_business_id must be 1 to 32 digits"))
    if isinstance(country, str) and country.strip().upper() == "US":
        return _blank(bad_request("TikTok Ad Library search does not support US"))
    chosen = _region(country, AD_COUNTRY) if country else None
    if isinstance(chosen, dict):
        return _blank(chosen)
    for label, value in (("start_date", start_date), ("end_date", end_date)):
        if value and not _DATE.fullmatch(value):
            return _blank(bad_request(f"{label} must be YYYY-MM-DD"))
    if bool(start_date) != bool(end_date):
        return _blank(bad_request("start_date and end_date must be sent together"))
    return _call("/v1/tiktok/ad-library/ads/search", {
        "query": text or None,
        "advertiserName": name or None,
        "advertiserBusinessId": business or None,
        "country": chosen,
        "startDate": start_date or None,
        "endDate": end_date or None,
        "cursor": cursor,
    })
