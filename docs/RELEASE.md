# Release checklist

Do not create a version tag and do not deploy until both of these have passed in the tag job of `.github/workflows/release.yml` on the commit you intend to ship. The operator form of this rule, including every required variable and the exact `--require` command, is in [RELEASE-OPERATOR.md](RELEASE-OPERATOR.md).

1. One live search, `GET /v1/tiktok/search`, returns at least one video with a public URL.
2. One live download of a public video reaches `ready`, exports a non-empty file under `SOCIAL_FETCH_DATA_DIR`, and returns a sha256.

A green unit test run is not either of those proofs. A skipped smoke is not either of those proofs. If the tag job is red, delete the tag if one was pushed and do not deploy that revision. This repository has no deploy job. Do not add one while the gate is red.

Adrian OS stays out of the release. Do not tag a build in order to register this server there. See [unregistered platforms](unregistered-platforms.md).

## Before a tag

The manual smoke stays skipped until `SOCIALFETCH_API_KEY` exists. It does not write `mcp-data/release-proof.json` when it skips. A tag push does not skip. `--require` fails closed when the key is missing or either live proof fails.

Run the smoke locally only when the key, network, ffmpeg, and at least 9 GiB free under `SOCIAL_FETCH_DATA_DIR` are all present:

```bash
pip install "git+https://github.com/Karnaf0katom/social-fetch.git"
SOCIAL_FETCH_DATA_DIR=./mcp-data PYTHONPATH=. python scripts/release_gate.py --smoke
```

`--check` only reads `mcp-data/release-proof.json`. It does not make the tag safe. The tag job runs the live search and the live download again and fails closed if either one fails.

## Required for the gate

`LIVE_DOWNLOAD_URL` defaults to `https://www.youtube.com/watch?v=jNQXAC9IVRw`. Override it with another public video URL if that one is unavailable. `LIVE_DOWNLOAD_TIMEOUT` defaults to 900 seconds. `LIVE_SEARCH_QUERY` defaults to `cat`. `SOCIALFETCH_API_KEY` is required before the smoke runs. `EASYDOWN_API_KEY` is not part of this smoke.

The integration workflow is separate. It stays skipped until its own secrets exist. A skipped integration run, and a skipped release smoke, must not be copied into the release proof.
