# Release checklist

Do not create a version tag and do not deploy until both of these have passed in `.github/workflows/release.yml` on the commit you intend to ship:

1. One live search, through the installed `FootageSearch`, returns at least one public row.
2. One live download of a public video reaches `ready`, exports a non-empty file, and returns a sha256.

A green unit test run is not either of those proofs. A skipped integration job is not either of those proofs. If the release workflow is red, delete the tag if one was pushed and do not deploy that revision. This repository has no deploy job. Do not add one while the gate is red.

Adrian OS stays out of the release. Do not tag a build in order to register this server there. See [unregistered platforms](unregistered-platforms.md).

## Before a tag

Run the gate locally only when the machine has network, ffmpeg, and at least 9 GiB free under `SOCIAL_FETCH_DATA_DIR`:

```bash
pip install "git+https://github.com/Karnaf0katom/social-fetch.git"
SOCIAL_FETCH_DATA_DIR=./mcp-data PYTHONPATH=. python scripts/release_gate.py --run
```

`--check` only reads `mcp-data/release-proof.json`. It does not make the tag safe. The tag workflow runs the live search and the live download again and fails closed if either one fails.

## Required for the gate

`LIVE_DOWNLOAD_URL` defaults to `https://www.youtube.com/watch?v=jNQXAC9IVRw`. Override it with another public video URL if that one is unavailable. `LIVE_DOWNLOAD_TIMEOUT` defaults to 900 seconds. `LIVE_SEARCH_QUERY` defaults to `cat`. No API key is required for these two proofs. `SOCIALFETCH_API_KEY` and `EASYDOWN_API_KEY` are required for their own tools, not for this gate.

The integration workflow is separate. It stays skipped until those keys exist. A skipped integration run must not be copied into the release proof.
