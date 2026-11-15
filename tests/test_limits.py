import io
import json
import unittest
import urllib.error

from research_mcp.util.api import _from_http
from research_mcp.util.limits import clamp_count, default_timeout


class LimitTests(unittest.TestCase):
    def test_clamp(self):
        self.assertEqual(clamp_count(0), 1)
        self.assertEqual(clamp_count(100), 50)
        self.assertEqual(clamp_count(-4), 1)
        self.assertEqual(clamp_count("nope", default=8), 8)
        self.assertEqual(clamp_count(100, hi=20), 20)

    def test_timeouts(self):
        self.assertEqual(default_timeout("metadata"), 60)
        self.assertEqual(default_timeout("download"), 900)


class ErrorTests(unittest.TestCase):
    def _http(self, status, body=None, headers=None):
        exc = urllib.error.HTTPError(
            "https://api.example.test/x",
            status,
            "boom",
            headers or {},
            io.BytesIO(json.dumps(body or {}).encode()),
        )
        return _from_http(exc, "https://api.example.test")

    def test_status_mapping(self):
        self.assertEqual(self._http(404)["error"], "not_found")
        self.assertEqual(self._http(401)["error"], "auth_failed")
        self.assertEqual(self._http(403)["detail"], "check API key")
        limited = self._http(429, headers={"Retry-After": "12"})
        self.assertEqual(limited["error"], "rate_limited")
        self.assertEqual(limited["retry_after"], 12)
        upstream = self._http(502, {"error": {"message": "down"}})
        self.assertEqual(upstream["error"], "upstream_error")
        self.assertTrue(upstream["retry"])
        self.assertEqual(upstream["status"], 502)

    def test_timeout_shape(self):
        from research_mcp.util.errors import relay_timeout

        out = relay_timeout("timed out")
        self.assertEqual(out["error"], "relay_timeout")
        self.assertTrue(out["retry"])


if __name__ == "__main__":
    unittest.main()
