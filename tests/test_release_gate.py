import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ReleaseGateTests(unittest.TestCase):
    def _env(self, directory: str) -> dict:
        env = {key: value for key, value in os.environ.items() if key != "SOCIALFETCH_API_KEY"}
        env["SOCIAL_FETCH_DATA_DIR"] = directory
        env["PYTHONPATH"] = str(ROOT)
        return env

    def test_check_blocks_without_proof(self):
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(
                [sys.executable, str(ROOT / "scripts/release_gate.py"), "--check"],
                cwd=directory,
                text=True,
                capture_output=True,
                env=self._env(directory),
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
                env=self._env(directory),
            )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_smoke_skips_without_key_and_writes_no_proof(self):
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(
                [sys.executable, str(ROOT / "scripts/release_gate.py"), "--smoke"],
                cwd=directory,
                text=True,
                capture_output=True,
                env=self._env(directory),
            )
            proof = Path(directory) / "release-proof.json"
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("release smoke skipped", result.stdout)
        self.assertFalse(proof.exists())

    def test_require_blocks_tagging_without_key(self):
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(
                [sys.executable, str(ROOT / "scripts/release_gate.py"), "--require"],
                cwd=directory,
                text=True,
                capture_output=True,
                env=self._env(directory),
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("tagging stays blocked", result.stderr)


if __name__ == "__main__":
    unittest.main()
