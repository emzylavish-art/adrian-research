# Release operator note

Do not create a `v*` tag and do not deploy until the gate below is green on the commit you intend to ship. A skipped smoke is not a pass. A green unit run is not a pass. This repository has no deploy job. Do not add one while the gate is red.

## Install

social-fetch is one line. Do not replace it with a guessed package name.

```bash
pip install "git+https://github.com/Karnaf0katom/social-fetch.git"
```

Python 3.10+ is required. The rest of the server install is `pip install -r requirements.txt`, which includes that same line plus `mcp>=1.9,<2`, `ddgs==9.14.4`, and `pytest>=8`. The release download also needs `ffmpeg` on the machine and at least 9 GiB free under `SOCIAL_FETCH_DATA_DIR`.

## Required environment

These have no usable default. The named operation fails or stays blocked if the variable is unset.

| Variable | Required for | If missing |
| --- | --- | --- |
| `PYTHONPATH` | Starting the server and the gate from this repository | Set it to `.` |
| `SOCIALFETCH_API_KEY` | Social Fetch REST, the live search, and the tag gate | Tools return an error and do not open a socket. `--require` exits 1. |
| `EASYDOWN_API_KEY` | EasyDown `POST /api/v1/parse` | EasyDown tools return an error and do not open a socket. Not part of the tag gate. |

The tag gate reads these as well. They have defaults, so an operator does not have to set them, but the download still lands under the data directory.

| Variable | Default | Gate use |
| --- | --- | --- |
| `SOCIAL_FETCH_DATA_DIR` | `./mcp-data` | Download export and `release-proof.json` |
| `LIVE_SEARCH_QUERY` | `cat` | Query for `GET /v1/tiktok/search` |
| `LIVE_DOWNLOAD_URL` | `https://www.youtube.com/watch?v=jNQXAC9IVRw` | Public video passed to `Client.download` |
| `LIVE_DOWNLOAD_TIMEOUT` | `900` | Seconds to wait for `ready` |

Server settings that are not part of the gate: `MCP_TRANSPORT` defaults to `stdio`, `HOST` to `0.0.0.0`, `PORT` to `8765`, `SOCIAL_FETCH_NS` to `research`, and `SOCIALFETCH_REGION` to `US` when a trending call omits its argument. The installed library may also read `FOOTAGE_DOWNLOAD_ROOT`, `FOOTAGE_SEARCH_PROVIDER`, `BRAVE_SEARCH_API_KEY`, `BRAVE_API_KEY`, `SERPER_API_KEY`, `SOCIAL_FETCH_COBALT_URL`, and `XDG_DATA_HOME`. Leave those unset unless you already use them.

GitHub secret names match the environment names: `SOCIALFETCH_API_KEY` and `EASYDOWN_API_KEY`. Do not put either value in the repository.

## Fail-closed gate

The blocking command is:

```bash
SOCIAL_FETCH_DATA_DIR=./mcp-data PYTHONPATH=. python scripts/release_gate.py --require
```

`--run` is the same command. A tag push of `v*` runs that command in `.github/workflows/release.yml` job `block-tag`. It does not skip.

The process blocks tagging and deploy unless both of these pass, in this order, on that command:

1. `SOCIALFETCH_API_KEY` is set. If it is not, the process prints `release gate blocked: SOCIALFETCH_API_KEY is not set; tagging stays blocked until one live search and one live download pass` and exits 1. It does not write a proof.
2. One live search, `GET https://api.socialfetch.dev/v1/tiktok/search`, returns at least one video whose `url` is present.
3. One live download of the public video reaches `ready`, exports a non-empty file under `SOCIAL_FETCH_DATA_DIR/downloads`, and returns a sha256 that matches the file.

Only then does it write `SOCIAL_FETCH_DATA_DIR/release-proof.json`. If the search fails, the download does not start. If the download fails, no proof is written. Delete a pushed `v*` tag if that job is red, and do not deploy that revision.

`--smoke` is not the gate. It prints `release smoke skipped: SOCIALFETCH_API_KEY is not set` and exits 0 when the key is missing. It writes no proof. `--check` only reads an existing proof. Neither one makes a tag safe.

Adrian OS is not part of this release. Do not tag in order to register the server there.
