import unittest

from research_mcp.util.schema import BASE_SCHEMA, normalize


class SchemaTests(unittest.TestCase):
    def test_every_key_present(self):
        out = normalize({"title": "hello", "author": {"username": "ada"}}, "tiktok", "https://in", "https://canon")
        for key in BASE_SCHEMA:
            self.assertIn(key, out)
        self.assertEqual(out["title"], "hello")
        self.assertEqual(out["author"]["username"], "ada")
        self.assertIsNone(out["author"]["bio"])
        self.assertEqual(out["platform"], "tiktok")
        self.assertEqual(out["canonical_url"], "https://canon")
        self.assertEqual(out["credits_charged"], 0)
        self.assertEqual(out["errors"], [])
        self.assertEqual(out["media"]["audio_urls"], [])

    def test_nested_merge_does_not_drop_defaults(self):
        out = normalize({"metrics": {"views": 3}, "media": {"video_urls": ["https://v"]}}, "youtube", "u", "c")
        self.assertEqual(out["metrics"]["views"], 3)
        self.assertIsNone(out["metrics"]["likes"])
        self.assertEqual(out["media"]["video_urls"], ["https://v"])
        self.assertIsNone(out["media"]["thumbnail_url"])

    def test_errors_are_appended(self):
        out = normalize({"errors": [{"error": "not_found"}]}, None, "u", "c", errors=[{"error": "relay_timeout"}])
        self.assertEqual([item["error"] for item in out["errors"]], ["not_found", "relay_timeout"])

    def test_template_is_not_mutated(self):
        normalize({"media": {"video_urls": ["https://v"]}, "comments_preview": [{"id": 1}]}, "x", "u", "c")
        self.assertEqual(BASE_SCHEMA["media"]["video_urls"], [])
        self.assertEqual(BASE_SCHEMA["comments_preview"], [])


if __name__ == "__main__":
    unittest.main()
