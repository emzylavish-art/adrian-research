import unittest
from unittest.mock import patch

from research_mcp.util.urls import canonicalize, detect_platform


class UrlTests(unittest.TestCase):
    def test_canonical_platforms(self):
        samples = {
            "https://www.tiktok.com/@name/video/123": "tiktok",
            "https://vt.tiktok.com/ZSabcd/": "tiktok",
            "https://www.tiktok.com/t/ZSabcd/": "tiktok",
            "https://www.youtube.com/watch?v=jNQXAC9IVRw": "youtube",
            "https://youtu.be/jNQXAC9IVRw": "youtube",
            "https://www.youtube.com/shorts/jNQXAC9IVRw": "youtube",
            "https://www.instagram.com/reel/C_bnaTAO2Ll": "instagram",
            "https://instagr.am/p/C_bnaTAO2Ll": "instagram",
            "https://x.com/name/status/1793226866335076588": "x",
            "https://t.co/abcDEF": "x",
            "https://www.facebook.com/page/videos/12345": "facebook",
            "https://www.facebook.com/share/v/abc": "facebook",
            "https://www.reddit.com/r/news/comments/1uwp60q": "reddit",
            "https://bsky.app/profile/bsky.app/post/3l3vgf77uco2g": "bluesky",
            "https://www.threads.net/@name/post/abc": "threads",
            "https://www.douyin.com/video/123": "douyin",
            "https://www.bilibili.com/video/BV1xx411c7mD": "bilibili",
            "https://www.weibo.com/12345/AbCd": "weibo",
            "https://www.kuaishou.com/short-video/abc123": "kuaishou",
            "https://www.xiaohongshu.com/explore/abc123": "xiaohongshu",
            "https://www.toutiao.com/i123456/": "toutiao",
        }
        for url, platform in samples.items():
            with self.subTest(url=url):
                self.assertEqual(detect_platform(url), platform)

    def test_unknown_domain_is_none(self):
        self.assertIsNone(detect_platform("https://example.com/post/1"))
        url, platform = canonicalize("https://example.com/post/1")
        self.assertEqual(url, "https://example.com/post/1")
        self.assertIsNone(platform)

    def test_canonical_does_not_open_network(self):
        url = "https://www.tiktok.com/@name/video/123"
        with patch("research_mcp.util.urls.urllib.request.urlopen") as opened:
            canonical, platform = canonicalize(url)
        opened.assert_not_called()
        self.assertEqual(canonical, url)
        self.assertEqual(platform, "tiktok")

    def test_short_link_uses_final_tiktok_url(self):
        class Response:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def geturl(self):
                return "https://www.tiktok.com/@name/video/999"

        with patch("research_mcp.util.urls.urllib.request.urlopen", return_value=Response()):
            canonical, platform = canonicalize("https://vt.tiktok.com/ZSabcd/")
        self.assertEqual(canonical, "https://www.tiktok.com/@name/video/999")
        self.assertEqual(platform, "tiktok")


if __name__ == "__main__":
    unittest.main()
