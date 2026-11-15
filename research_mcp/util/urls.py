"""Domain routing for public social URLs. No network call unless the URL is a known short link."""
from __future__ import annotations

import re
import socket
import urllib.error
import urllib.parse
import urllib.request

RESOLVERS = {
    "tiktok": {
        "short": re.compile(r"^https?://(?:vt|vm)\.tiktok\.com/\S+$"),
        "t_link": re.compile(r"^https?://(?:www\.)?tiktok\.com/t/\S+$"),
        "canonical": re.compile(r"^https?://(?:www\.)?tiktok\.com/@[^/]+/video/\d+"),
    },
    "youtube": {
        "short": re.compile(r"^https?://youtu\.be/\S+$"),
        "canonical": re.compile(r"^https?://(?:www\.)?youtube\.com/watch\?v=[\w-]+"),
        "shorts": re.compile(r"^https?://(?:www\.)?youtube\.com/shorts/[\w-]+"),
    },
    "instagram": {
        "short": re.compile(r"^https?://instagr\.am/\S+$"),
        "canonical": re.compile(r"^https?://(?:www\.)?instagram\.com/(?:p|reel|tv)/[^/?#]+"),
    },
    "x": {
        "short": re.compile(r"^https?://t\.co/\S+$"),
        "canonical": re.compile(r"^https?://(?:www\.)?(?:x|twitter)\.com/[^/]+/status/\d+"),
    },
    "facebook": {
        "canonical": re.compile(r"^https?://(?:www\.)?facebook\.com/.+/videos/\d+"),
        "share": re.compile(r"^https?://(?:www\.)?facebook\.com/share/v/\S+"),
        "watch": re.compile(r"^https?://(?:www\.)?facebook\.com/watch/?\?"),
    },
    "reddit": {
        "canonical": re.compile(r"^https?://(?:www\.)?reddit\.com/r/[\w-]+/comments/\w+"),
    },
    "bluesky": {
        "canonical": re.compile(r"^https?://bsky\.app/profile/[^/]+/post/\S+"),
    },
    "threads": {
        "canonical": re.compile(r"^https?://(?:www\.)?threads\.(?:net|com)/(?:t/|@[^/]+/post/)\S+"),
    },
    "douyin": {
        "short": re.compile(r"^https?://v\.douyin\.com/\S+$"),
        "canonical": re.compile(r"^https?://(?:www\.)?douyin\.com/video/\d+"),
    },
    "bilibili": {
        "short": re.compile(r"^https?://b23\.tv/\S+$"),
        "canonical": re.compile(r"^https?://(?:www\.)?bilibili\.com/video/(?:BV|av)\w+"),
    },
    "weibo": {
        "canonical": re.compile(r"^https?://(?:www\.)?weibo\.com/\d+/\w+"),
    },
    "kuaishou": {
        "short": re.compile(r"^https?://v\.kuaishou\.com/\S+$"),
        "canonical": re.compile(r"^https?://(?:www\.)?kuaishou\.com/short-video/\w+"),
    },
    "xiaohongshu": {
        "short": re.compile(r"^https?://xhslink\.com/\S+$"),
        "canonical": re.compile(r"^https?://(?:www\.)?xiaohongshu\.com/(?:explore|discovery/item)/\S+"),
    },
    "toutiao": {
        "canonical": re.compile(r"^https?://(?:www\.)?toutiao\.com/(?:i\d+|video/\d+)"),
    },
}

HOSTS = {
    "tiktok.com": "tiktok",
    "vt.tiktok.com": "tiktok",
    "vm.tiktok.com": "tiktok",
    "youtube.com": "youtube",
    "youtu.be": "youtube",
    "instagram.com": "instagram",
    "instagr.am": "instagram",
    "x.com": "x",
    "twitter.com": "x",
    "t.co": "x",
    "facebook.com": "facebook",
    "reddit.com": "reddit",
    "bsky.app": "bluesky",
    "threads.net": "threads",
    "threads.com": "threads",
    "douyin.com": "douyin",
    "v.douyin.com": "douyin",
    "bilibili.com": "bilibili",
    "b23.tv": "bilibili",
    "weibo.com": "weibo",
    "kuaishou.com": "kuaishou",
    "v.kuaishou.com": "kuaishou",
    "xiaohongshu.com": "xiaohongshu",
    "xhslink.com": "xiaohongshu",
    "toutiao.com": "toutiao",
}

_SHORT_KEYS = ("short", "t_link", "share")


def _host(url: str) -> str:
    host = urllib.parse.urlparse(url).netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    return host


def detect_platform(url: str) -> str | None:
    if not isinstance(url, str) or not url.strip():
        return None
    text = url.strip()
    for platform, patterns in RESOLVERS.items():
        for pattern in patterns.values():
            if pattern.match(text):
                return platform
    return HOSTS.get(_host(text))


def _known_host(url: str) -> bool:
    return _host(url) in HOSTS


def canonicalize(url: str, timeout: int = 15) -> tuple[str, str | None]:
    """Resolve a known short link. Returns (canonical_url, platform). Unknown domains stay unchanged."""
    text = url.strip() if isinstance(url, str) else ""
    platform = detect_platform(text)
    if platform is None or not text:
        return text, None
    patterns = RESOLVERS.get(platform, {})
    canonical = patterns.get("canonical") or patterns.get("shorts")
    if canonical and canonical.match(text):
        return text, platform
    if patterns.get("shorts") and patterns["shorts"].match(text):
        return text, platform
    needs_head = any(patterns.get(key) and patterns[key].match(text) for key in _SHORT_KEYS)
    if not needs_head:
        return text, platform
    request = urllib.request.Request(text, method="HEAD", headers={"User-Agent": "tiktok-research-mcp/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            final = response.geturl()
    except (urllib.error.URLError, TimeoutError, socket.timeout, ValueError):
        return text, platform
    if not _known_host(final):
        return text, platform
    return final, detect_platform(final) or platform
