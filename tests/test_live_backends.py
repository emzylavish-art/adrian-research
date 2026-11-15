"""Live backend checks. Unit CI does not set RUN_LIVE, so these stay skipped."""
import os
import unittest
import urllib.error
import urllib.request

from research_mcp.util.api import EASYDOWN_BASE, SOCIALFETCH_BASE


class LiveBackendTests(unittest.TestCase):
    def test_socialfetch_whoami(self):
        if os.getenv("RUN_LIVE") != "1" or not os.getenv("SOCIALFETCH_API_KEY"):
            self.skipTest("skipped until SOCIALFETCH_API_KEY is set and RUN_LIVE=1")
        request = urllib.request.Request(
            SOCIALFETCH_BASE + "/v1/whoami",
            headers={"x-api-key": os.environ["SOCIALFETCH_API_KEY"], "Accept": "application/json"},
        )
        with urllib.request.urlopen(request, timeout=60) as response:
            self.assertEqual(response.status, 200)
            body = response.read()
        self.assertTrue(body)

    def test_easydown_accepts_bearer(self):
        if os.getenv("RUN_LIVE") != "1" or not os.getenv("EASYDOWN_API_KEY"):
            self.skipTest("skipped until EASYDOWN_API_KEY is set and RUN_LIVE=1")
        payload = b'{"url":"https://www.tiktok.com/@tiktok/video/6718335390845095173"}'
        request = urllib.request.Request(
            EASYDOWN_BASE + "/api/v1/parse",
            data=payload,
            headers={
                "Authorization": f"Bearer {os.environ['EASYDOWN_API_KEY']}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                status = response.status
        except urllib.error.HTTPError as exc:
            if exc.code in (401, 403):
                self.fail("EasyDown rejected the bearer token")
            status = exc.code
        self.assertLess(status, 500)


if __name__ == "__main__":
    unittest.main()
