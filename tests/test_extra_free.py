import json
import unittest
from unittest.mock import patch
import os
from urllib.error import HTTPError

from research_mcp.backends import linkedin_free, odysee_free, pinterest_free, rumble_free, youtube_free
from research_mcp.router import route
from research_mcp.util.service import get_post


class _Response:
    def __init__(self, status, body, url):
        self.status = status
        self._body = body
        self._url = url

    def read(self, _n=None):
        return self._body if isinstance(self._body, bytes) else self._body.encode()

    def geturl(self):
        return self._url

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class ExtraFreeTests(unittest.TestCase):
    def test_linkedin_429_is_terminal(self):
        def boom(*args, **kwargs):
            raise HTTPError("https://www.linkedin.com/in/x", 429, "too many", hdrs=None, fp=None)

        with patch("research_mcp.backends.linkedin_free.urllib.request.urlopen", side_effect=boom) as opened:
            out = linkedin_free.get_profile("https://www.linkedin.com/in/x")
        self.assertEqual(opened.call_count, 1)
        self.assertEqual(out["path_used"], "free")
        self.assertEqual(out["credits_charged"], 0)
        self.assertEqual(out["errors"][0]["error"], "rate_limited")

    def test_linkedin_meta_name(self):
        html = '<html><meta property="og:title" content="Ada Lovelace - Analyst | LinkedIn"></html>'
        with patch("research_mcp.backends.linkedin_free.urllib.request.urlopen", return_value=_Response(200, html, "https://www.linkedin.com/in/ada")):
            out = linkedin_free.get_profile("https://www.linkedin.com/in/ada")
        self.assertEqual(out["data"]["name"], "Ada Lovelace")
        self.assertEqual(out["data"]["headline"], "Analyst")
        self.assertIsNone(out["data"]["followers"])

    def test_odysee_maps_title_and_does_not_invent_views(self):
        payload = {"result": {"lbry://x": {"value": {"title": "Hello", "description": "A clip"}, "signing_channel": {"name": "@news"}, "meta": {"reposted": 0}}}}
        with patch("research_mcp.backends.odysee_free.urllib.request.urlopen", return_value=_Response(200, json.dumps(payload), "https://api.na-backend.odysee.com/api/v1/proxy")):
            out = odysee_free.get_video("https://odysee.com/@news/hello")
        self.assertEqual(out["data"]["title"], "Hello")
        self.assertIsNone(out["data"]["view_count"])
        self.assertTrue(any("view count" in item["detail"] for item in out["errors"]))

    def test_pinterest_pinresource_fields(self):
        payload = {"resource_response": {"data": {"title": "Cat", "description": "A pin", "images": {"orig": {"url": "https://img.example/a.jpg"}}, "pinner": {"username": "ada"}, "board": {"name": "Pets"}}}}
        with patch("research_mcp.backends.pinterest_free.urllib.request.urlopen", return_value=_Response(200, json.dumps(payload), "https://www.pinterest.com/resource/PinResource/get/")):
            out = pinterest_free.get_pin("https://www.pinterest.com/pin/42/")
        self.assertEqual(out["data"]["title"], "Cat")
        self.assertEqual(out["data"]["author"], "ada")
        self.assertEqual(out["data"]["board"], "Pets")
        self.assertEqual(out["source_name"], "pinterest-pinresource")

    def test_rumble_challenge_does_not_invent_views(self):
        saved = {"status": "blocked", "message": "Just a moment..."}
        with patch("research_mcp.backends.rumble_free.resource", return_value=saved):
            out = rumble_free.get_video("https://rumble.com/v1.html")
        self.assertEqual(out["errors"][0]["error"], "blocked")
        self.assertIsNone(out["data"]["view_count"])

    def test_youtube_counts_are_integers(self):
        payload = {"likes": 3, "dislikes": 1}
        with patch("research_mcp.backends.youtube_free.urllib.request.urlopen", return_value=_Response(200, json.dumps(payload), "https://returnyoutubedislikeapi.com/votes")):
            out = youtube_free.get_counts("jNQXAC9IVRw")
        self.assertEqual(out["data"]["likes"], 3)
        self.assertEqual(out["data"]["dislikes"], 1)
        self.assertEqual(out["credits_charged"], 0)

    def test_youtube_get_post_uses_counts_when_easydown_key_is_missing(self):
        empty = ({}, [{"error": "api_key_missing", "detail": "no key configured for https://api.easydown.org"}], 0)
        counts = {
            "data": {"likes": 5, "dislikes": 1},
            "source_name": "returnyoutubedislike",
            "errors": [],
            "path_used": "free",
            "credits_charged": 0,
        }
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("EASYDOWN_API_KEY", None)
            with patch("research_mcp.util.service._fill", return_value=empty):
                with patch("research_mcp.backends.youtube_free.get_counts", return_value=counts):
                    out = get_post("https://www.youtube.com/watch?v=jNQXAC9IVRw")
        self.assertEqual(out["path_used"], "free")
        self.assertEqual(out["source_detail"], "returnyoutubedislike")
        self.assertEqual(out["metrics"]["likes"], 5)
        self.assertEqual(out["metrics"]["dislikes"], 1)
        self.assertEqual(out["credits_charged"], 0)
        self.assertIsNone(out["title"])
        self.assertTrue(any(item.get("error") == "api_key_missing" for item in out["errors"]))

    def test_youtube_get_post_does_not_replace_easydown_when_key_is_set(self):
        filled = ({"title": "Clip", "metrics": {"likes": 9}}, [], 3)
        with patch.dict(os.environ, {"EASYDOWN_API_KEY": "ed_test"}):
            with patch("research_mcp.util.service._fill", return_value=filled):
                with patch("research_mcp.backends.youtube_free.get_counts") as counts:
                    out = get_post("https://www.youtube.com/watch?v=jNQXAC9IVRw")
        counts.assert_not_called()
        self.assertEqual(out["title"], "Clip")
        self.assertEqual(out["metrics"]["likes"], 9)
        self.assertIsNone(out["path_used"])

    def test_missing_tiktok_scraper_keeps_existing_path(self):
        empty = {"data": {}, "source_name": "omkarcloud-tiktok", "errors": [{"error": "request_failed"}], "path_used": "free", "credits_charged": 0}
        with patch("research_mcp.router.tiktok_video", return_value=empty):
            self.assertIsNone(route("get_post", url="https://www.tiktok.com/@name/video/1"))

    def test_router_uses_verified_tiktok_counts(self):
        found = {"data": {"play_count": 12, "play_link": "https://cdn.example/a.mp4"}, "source_name": "omkarcloud-tiktok", "errors": [], "path_used": "free", "credits_charged": 0}
        with patch("research_mcp.router.tiktok_video", return_value=found):
            out = route("get_post", url="https://www.tiktok.com/@name/video/1")
        self.assertEqual(out["path_used"], "free")
        self.assertEqual(out["metrics"]["views"], 12)
        self.assertEqual(out["credits_charged"], 0)
        self.assertEqual(out["media"]["video_urls"], ["https://cdn.example/a.mp4"])

    def test_router_returns_free_odysee_without_a_key(self):
        payload = {"data": {"title": "Hello"}, "source_name": "odysee-proxy", "errors": [], "path_used": "free", "credits_charged": 0}
        with patch.dict("os.environ", {}, clear=False):
            with patch("research_mcp.router.odysee_video", return_value=payload):
                out = route("get_post", url="https://odysee.com/@a/b")
        self.assertEqual(out["path_used"], "free")
        self.assertEqual(out["credits_charged"], 0)
        self.assertEqual(out["title"], "Hello")
        self.assertEqual(out["source_detail"], "odysee-proxy")


if __name__ == "__main__":
    unittest.main()
