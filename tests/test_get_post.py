import os
import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch

from research_mcp.util.schema import BASE_SCHEMA
from research_mcp.util import service


ROOT = Path(__file__).resolve().parents[1]


class GetPostTests(unittest.TestCase):
    def test_missing_socialfetch_key_falls_through_without_network(self):
        os.environ.pop("SOCIALFETCH_API_KEY", None)
        os.environ.pop("EASYDOWN_API_KEY", None)
        with patch("research_mcp.util.service._library", return_value={"text": "caption text", "title": "Local"}):
            with patch("research_mcp.util.api.urllib.request.urlopen") as opened:
                out = service.get_post("https://www.tiktok.com/@name/video/123")
        opened.assert_not_called()
        self.assertEqual(out["platform"], "tiktok")
        self.assertEqual(out["description"], "caption text")
        self.assertTrue(any(item.get("error") == "api_key_missing" for item in out["errors"]))
        for key in BASE_SCHEMA:
            self.assertIn(key, out)

    def test_tiktok_rest_used_when_key_present(self):
        payload = {
            "data": {
                "lookupStatus": "found",
                "video": {"id": "123", "url": "https://www.tiktok.com/@name/video/123", "caption": "hi", "mediaType": "video", "durationMs": 1000, "isAd": False},
                "author": {"handle": "name", "nickname": "Name"},
                "metrics": {"views": 4, "likes": 1, "comments": 0, "shares": 0, "saves": 0},
                "media": {"thumbnailUrl": "https://img.example/t.jpg", "downloadUrl": "https://media.example/v.mp4"},
            },
            "meta": {"creditsCharged": 1},
        }
        with patch.dict(os.environ, {"SOCIALFETCH_API_KEY": "sfk_test"}):
            with patch("research_mcp.util.service.api_get", return_value=payload) as called:
                out = service.get_post("https://www.tiktok.com/@name/video/123")
        self.assertEqual(called.call_args.args[1], "/v1/tiktok/videos")
        self.assertEqual(out["title"], "hi")
        self.assertEqual(out["credits_charged"], 1)
        self.assertEqual(out["metrics"]["views"], 4)
        self.assertEqual(out["errors"], [])

    def test_dead_lookup_is_not_found(self):
        payload = {"data": {"lookupStatus": "not_found", "video": None}, "meta": {"creditsCharged": 1}}
        with patch.dict(os.environ, {"SOCIALFETCH_API_KEY": "sfk_test"}):
            with patch("research_mcp.util.service.api_get", return_value=payload):
                out = service.get_post("https://www.tiktok.com/@name/video/0")
        self.assertEqual(out["errors"][0]["error"], "not_found")

    def test_bluesky_uses_documented_post_route(self):
        payload = {
            "data": {
                "lookupStatus": "found",
                "post": {"url": "https://bsky.app/profile/name/post/abc", "text": "hello", "createdAt": "2025-01-01T00:00:00Z"},
                "author": {"handle": "name", "displayName": "Name", "verified": False},
                "metrics": {"likes": 2, "reposts": 1, "replies": 0, "quotes": 0},
                "embed": {"kind": "external", "video": None, "images": None},
                "replies": [],
            },
            "meta": {"creditsCharged": 1},
        }
        with patch.dict(os.environ, {"SOCIALFETCH_API_KEY": "sfk_test"}):
            with patch("research_mcp.util.service.api_get", return_value=payload) as called:
                out = service.get_post("https://bsky.app/profile/name/post/abc")
        self.assertEqual(called.call_args.args[1], "/v1/bluesky/posts")
        self.assertEqual(out["platform"], "bluesky")
        self.assertEqual(out["title"], "hello")
        self.assertEqual(out["credits_charged"], 1)
        self.assertEqual(out["metrics"]["reposts"], 1)

    def test_trending_other_platform_does_not_call_network(self):
        with patch("research_mcp.util.service.api_get") as called:
            out = service.get_trending("youtube")
        called.assert_not_called()
        self.assertEqual(out["errors"][0]["error"], "unsupported_platform")

    def test_original_server_text_preserved(self):
        current = (ROOT / "research_mcp/server.py").read_text()
        original = subprocess.check_output(["git", "show", "main:research_mcp/server.py"], cwd=ROOT, text=True)
        marker = '\nif __name__ == "__main__":\n'
        head, tail = original.split(marker, 1)
        self.assertTrue(current.startswith(head.rstrip() + "\n"))
        self.assertTrue(current.endswith(marker + tail))
        self.assertIn("def search_videos(", head)
        self.assertNotIn("def get_post(", head)

    def test_appended_tools_register(self):
        from research_mcp.server import mcp

        names = {tool.name for tool in mcp._tool_manager.list_tools()}
        self.assertIn("search_videos", names)
        self.assertIn("get_post", names)
        self.assertNotIn("get_tiktok_video", names)
        self.assertEqual(mcp.name, "adrian-research")


if __name__ == "__main__":
    unittest.main()
