import os
import unittest
from unittest.mock import patch

from research_mcp.util import tiktok


class TikTokNextTests(unittest.TestCase):
    def test_missing_key_does_not_call_network(self):
        os.environ.pop("SOCIALFETCH_API_KEY", None)
        with patch("research_mcp.util.api.urllib.request.urlopen") as opened:
            out = tiktok.search_tiktok_videos("cats")
        opened.assert_not_called()
        self.assertEqual(out["errors"][0]["error"], "api_key_missing")
        self.assertEqual(out["results"], [])

    def test_native_search_path_is_not_search_videos(self):
        with patch.dict(os.environ, {"SOCIALFETCH_API_KEY": "sfk_test"}):
            with patch("research_mcp.util.tiktok.api_get", return_value={"data": {"videos": [{"url": "https://www.tiktok.com/@a/video/1"}], "page": {"nextCursor": "2", "hasMore": True}}, "meta": {"creditsCharged": 1}}) as called:
                out = tiktok.search_tiktok_videos("cats", date_posted="this-week", sort_by="most-liked", region="us")
        self.assertEqual(called.call_args.args[1], "/v1/tiktok/search")
        self.assertEqual(called.call_args.args[2]["datePosted"], "this-week")
        self.assertEqual(called.call_args.args[2]["region"], "US")
        self.assertEqual(out["credits_charged"], 1)
        self.assertTrue(out["has_more"])

    def test_audience_requires_confirm(self):
        with patch("research_mcp.util.tiktok.api_get") as called:
            out = tiktok.get_tiktok_audience("name")
        called.assert_not_called()
        self.assertEqual(out["errors"][0]["error"], "bad_request")
        self.assertIn("30", out["errors"][0]["detail"])

    def test_ad_search_rejects_us(self):
        with patch("research_mcp.util.tiktok.api_get") as called:
            out = tiktok.search_tiktok_ads(query="nike", country="US")
        called.assert_not_called()
        self.assertIn("US", out["errors"][0]["detail"])

    def test_followers_path(self):
        with patch.dict(os.environ, {"SOCIALFETCH_API_KEY": "sfk_test"}):
            with patch("research_mcp.util.tiktok.api_get", return_value={"data": {"lookupStatus": "hidden", "followers": [], "page": {"nextCursor": None, "hasMore": False}}, "meta": {"creditsCharged": 1}}) as called:
                out = tiktok.list_tiktok_followers("@name")
        self.assertEqual(called.call_args.args[1], "/v1/tiktok/profiles/name/followers")
        self.assertEqual(out["errors"][0]["error"], "not_found")
        self.assertEqual(out["errors"][0]["detail"], "hidden")

    def test_original_entry_points_remain(self):
        from research_mcp import server

        self.assertTrue(callable(server.search_videos))
        self.assertTrue(callable(server.main))
        names = {tool.name for tool in server.mcp._tool_manager.list_tools()}
        self.assertIn("search_videos", names)
        self.assertIn("search_tiktok_videos", names)
        self.assertIn("get_tiktok_audience", names)
        self.assertNotIn("get_tiktok_video", names)


if __name__ == "__main__":
    unittest.main()
