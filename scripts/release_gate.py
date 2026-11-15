"""Block a tag or deploy until one live search and one live download pass.

`--smoke` skips with exit 0 when SOCIALFETCH_API_KEY is missing. It does not
write a proof. `--require` is the tag gate: a missing key blocks, it does not skip.
`--check` only reads a proof file and is not sufficient for a release.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_URL = "https://www.youtube.com/watch?v=jNQXAC9IVRw"
NEED_FREE = 9 * 1024**3
SEARCH_URL = "https://api.socialfetch.dev/v1/tiktok/search"


def proof_path() -> Path:
    root = Path(os.getenv("SOCIAL_FETCH_DATA_DIR", "./mcp-data"))
    return root / "release-proof.json"


def fail(message: str) -> None:
    print(f"release gate blocked: {message}", file=sys.stderr)
    raise SystemExit(1)


def check() -> None:
    path = proof_path()
    if not path.is_file():
        fail(f"missing {path}. Run with --run after a live search and a live download.")
    try:
        proof = json.loads(path.read_text())
    except (OSError, ValueError) as exc:
        fail(f"unreadable proof: {exc}")
    search = proof.get("search") if isinstance(proof, dict) else None
    download = proof.get("download") if isinstance(proof, dict) else None
    if not isinstance(search, dict) or not search.get("ok") or not search.get("url"):
        fail("proof has no passing live search")
    if not isinstance(download, dict) or not download.get("ok") or not download.get("sha256"):
        fail("proof has no passing live download")
    print(f"release proof present: {path}")


def live_search() -> dict:
    key = os.getenv("SOCIALFETCH_API_KEY")
    if not key:
        fail("SOCIALFETCH_API_KEY is not set")
    query = os.getenv("LIVE_SEARCH_QUERY", "cat")
    target = SEARCH_URL + "?" + urllib.parse.urlencode({"query": query})
    request = urllib.request.Request(
        target,
        headers={"x-api-key": key, "Accept": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        payload = json.loads(response.read().decode())
    data = payload.get("data") if isinstance(payload, dict) else None
    videos = data.get("videos") if isinstance(data, dict) else None
    if not isinstance(videos, list) or not videos:
        fail("live search returned no videos")
    url = videos[0].get("url") if isinstance(videos[0], dict) else None
    if not url:
        fail("live search video had no url")
    meta = payload.get("meta") if isinstance(payload, dict) else None
    charged = meta.get("creditsCharged") if isinstance(meta, dict) else None
    return {"ok": True, "query": query, "url": url, "count": len(videos), "credits_charged": charged}


def live_download() -> dict:
    if shutil.which("ffmpeg") is None:
        fail("ffmpeg is not installed")
    root = Path(os.getenv("SOCIAL_FETCH_DATA_DIR", "./mcp-data"))
    root.mkdir(parents=True, exist_ok=True)
    free = shutil.disk_usage(root).free
    if free < NEED_FREE:
        fail(f"need 9 GiB free under {root}, found {free} bytes")
    from social_fetch import Client

    url = os.getenv("LIVE_DOWNLOAD_URL", DEFAULT_URL)
    timeout = int(os.getenv("LIVE_DOWNLOAD_TIMEOUT", "900"))
    client = Client(data_dir=str(root), namespace="release-gate")
    job = client.download(url, wait=True, timeout=timeout)
    if not isinstance(job, dict) or job.get("status") != "ready" or "id" not in job:
        fail(f"download did not become ready: {job!r}")
    destination = root / "downloads"
    destination.mkdir(parents=True, exist_ok=True)
    out = destination / f"{job['id']}.mp4"
    exported = client.export(job["id"], out)
    digest = hashlib.sha256(out.read_bytes()).hexdigest() if out.is_file() and out.stat().st_size else ""
    recorded = exported.get("sha256") if isinstance(exported, dict) else None
    if not digest or (recorded and recorded != digest):
        fail(f"export did not produce a hashed file: {exported!r}")
    return {"ok": True, "url": url, "job_id": job["id"], "bytes": out.stat().st_size, "sha256": digest}


def run() -> None:
    if not os.getenv("SOCIALFETCH_API_KEY"):
        fail("SOCIALFETCH_API_KEY is not set; tagging stays blocked until one live search and one live download pass")
    search = live_search()
    download = live_download()
    path = proof_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({
        "created_at": datetime.now(timezone.utc).isoformat(),
        "search": search,
        "download": download,
    }, indent=2) + "\n")
    print(f"release proof written: {path}")


def smoke() -> None:
    if not os.getenv("SOCIALFETCH_API_KEY"):
        print("release smoke skipped: SOCIALFETCH_API_KEY is not set")
        return
    run()


def main() -> None:
    parser = argparse.ArgumentParser(description="Block tagging and deploy until live proofs pass.")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="Fail unless a proof file already exists.")
    mode.add_argument("--smoke", action="store_true", help="Skip when the Social Fetch key is missing. Otherwise run both live proofs.")
    mode.add_argument("--require", action="store_true", help="Fail closed. A missing key blocks tagging.")
    mode.add_argument("--run", action="store_true", help="Alias of --require.")
    args = parser.parse_args()
    if args.check:
        check()
    elif args.smoke:
        smoke()
    else:
        run()


if __name__ == "__main__":
    main()
