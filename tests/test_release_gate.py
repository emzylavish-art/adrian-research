import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ReleaseGateTests(unittest.TestCase):
    def test_check_blocks_without_proof(self):
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(
                [sys.executable, str(ROOT / "scripts/release_gate.py"), "--check"],
                cwd=directory,
                text=True,
                capture_output=True,
                env={**os.environ, "SOCIAL_FETCH_DATA_DIR": directory, "PYTHONPATH": str(ROOT)},
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("release gate blocked", result.stderr)

    def test_check_accepts_complete_proof(self):
        with tempfile.TemporaryDirectory() as directory:
            proof = Path(directory) / "release-proof.json"
            proof.write_text(json.dumps({
                "search": {"ok": True, "url": "https://www.tiktok.com/@name/video/1"},
                "download": {"ok": True, "sha256": "abc"},
            }))
            result = subprocess.run(
                [sys.executable, str(ROOT / "scripts/release_gate.py"), "--check"],
                cwd=directory,
                text=True,
                capture_output=True,
                env={**os.environ, "SOCIAL_FETCH_DATA_DIR": directory, "PYTHONPATH": str(ROOT)},
            )
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
