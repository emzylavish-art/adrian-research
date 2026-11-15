import os
import unittest
from unittest.mock import patch

from research_mcp.util.easydown import easydown_parse
from research_mcp.util.schema import BASE_SCHEMA
from research_mcp.util.service import _map_easydown, get_post


class EasyDownTests(unittest.TestCase):
    def test_missing_key_does_not_call_network(self):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("EASYDOWN_API_KEY", None)
            with patch("research_mcp.util.api.urllib.request.urlopen") as opened:
                out = easydown_parse("https://www.youtube.com/watch?v=jNQXAC9IVRw", "youtube")
        opened.assert_not_called()
        self.assertEqual(out["error"], "api_key_missing")

    def test_platform_route(self):
        with patch.dict(os.environ, {"EASYDOWN_API_KEY": "ed_test"}):
            with patch("research_mcp.util.easydown.api_post", return_value={"status": 200}) as posted:
                easydown_parse("https://x.com/name/status/1", "x")
        posted.assert_called_once()
        self.assertEqual(posted.call_args.args[1], "/api/v1/platforms/twitter/parse")
        self.assertEqual(posted.call_args.args[2], {"url": "https://x.com/name/status/1"})

    def test_mapping_fills_schema(self):
        payload = {
            "status": 200,
            "msg": "success",
            "data": {
                "media": {
                    "platform": "youtube",
                    "title": "Clip",
                    "thumbnail": "https://img.example/t.jpg",
                    "duration": 2,
                    "images": [{"url": "https://img.example/a.jpg", "width": 1, "height": 1}],
                    "videos": [{
                        "url": "https://media.example/v.mp4",
                        "quality": "360p",
                        "mimeType": "video/mp4",
                        "width": 480,
                        "height": 360,
                        "hasAudio": True,
                        "source": "direct",
                    }],
                    "audios": [{
                        "url": "https://media.example/a.m4a",
                        "quality": "medium",
                        "mimeType": "audio/mp4",
                        "bitrate": 128000,
                        "source": "adaptive",
                    }],
                },
                "platformData": {"author": {"unique_id": "ada", "nickname": "Ada"}, "statistics": {"play_count": 9}},
            },
        }
        mapped = _map_easydown(payload)
        out = __import__("research_mcp.util.schema", fromlist=["normalize"]).normalize(mapped, "youtube", "u", "c")
        for key in BASE_SCHEMA:
            self.assertIn(key, out)
        self.assertEqual(out["media"]["video_urls"], ["https://media.example/v.mp4"])
        self.assertEqual(out["media"]["image_urls"], ["https://img.example/a.jpg"])
        self.assertEqual(out["media"]["audio_urls"], ["https://media.example/a.m4a"])
        self.assertEqual(out["author"]["username"], "ada")
        self.assertEqual(out["metrics"]["views"], 9)
        self.assertEqual(out["media"]["duration_ms"], 2000)

    def test_get_post_unknown_domain(self):
        out = get_post("https://example.com/nope")
        self.assertEqual(out["errors"][0]["error"], "unsupported_platform")
        self.assertIsNone(out["platform"])
        for key in BASE_SCHEMA:
            self.assertIn(key, out)


if __name__ == "__main__":
    unittest.main()
