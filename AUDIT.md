# Phase 0 audit

Audited 2026-11-15 before the universal layer was appended. This is the ground truth for `feature/universal-social-layer`. Nothing here was tested by downloading a full video. Live relay downloads were not run.

## Existing server

`research_mcp/server.py` on `main` is 60 lines. It was not rewritten.

- Imports: `__future__.annotations`, `os`, `re`, `FastMCP`, `FootageSearch`.
- The original constructor name was changed to `adrian-research` when the repository was renamed. Host, port, `stateless_http`, and `json_response` were not changed.
- `_search = FootageSearch.from_env(include_catalogs=False)`.
- `_VIDEO = re.compile(r"tiktok\.com/@([^/]+)/video/(\d+)")`.
- One tool, `search_videos(query, count=10)`. It clamps count to 1..20, searches `source="tiktok"`, and returns `url`, `video_id`, `title`, `description`, `username`. It raises `ValueError` on an empty query. That behavior is unchanged.
- `main()` calls `mcp.run(transport=MCP_TRANSPORT or "stdio")`.
- `if __name__ == "__main__": main()` is unchanged and remains the last statement. New tools are registered above it so `python -m research_mcp.server` sees them.

`requirements.txt` keeps `mcp>=1.9,<2`, `ddgs==9.14.4`, and `git+https://github.com/Karnaf0katom/social-fetch.git`. That git URL installed in this session, so it was not replaced. `pytest>=8` was added because the closing note asked for a declared runner. Runtime HTTP calls still use the standard library.

`app.py` imports `mcp` and exposes `mcp.streamable_http_app()`. `vercel.json` only sets `app.py` `maxDuration` to 60. Neither file was edited. A `download_media` call with `wait=True` will not fit in that 60 second limit. Local stdio can wait. Vercel callers should use `wait=False` and `media_status`.

There were no existing tests.

## social-fetch

Installed from the git URL in `requirements.txt`. `Client.download`, `Client.export`, `Client.status`, `Client.resource`, `Client.account`, and `Client.download_image` are present.

`social_link` recognized these public examples as video links without downloading them: TikTok canonical, `vt.tiktok.com`, YouTube watch, `youtu.be`, Instagram reel, X status, Facebook watch, Reddit comments, Bluesky post.

Download domains in the installed library are youtube, instagram, tiktok, x, facebook, reddit, bluesky, pinterest, twitch, snapchat, linkedin, and mastodon. `Client.comments` accepts Instagram and Reddit posts only. `Client.download_image` accepts native Reddit images only. Account samples are bounded and provider dependent. The library README says Instagram returned three posts in its launch check and YouTube account browsing was unavailable.

A full download was not run. Each active download wants about 9 GiB free, ffmpeg, and an external relay. This sandbox audit recorded recognition, not a successful MP4 export. Do not treat recognition as a download proof.

`FootageSearch.search` accepts `source`. With `include_catalogs=False`, indexed social sources are the same twelve domains. `search_videos` still calls it with `source="tiktok"` only.

## Social Fetch REST

Base `https://api.socialfetch.dev`. Auth header `x-api-key`. TikTok routes used by this layer are the documented ones, including `/v1/tiktok/videos`, `/v1/tiktok/videos/transcript`, `/v1/tiktok/videos/comments`, `/v1/tiktok/videos/comments/replies`, `/v1/tiktok/profiles/{handle}`, `/v1/tiktok/profiles/{handle}/videos`, `/v1/tiktok/feed/trending`, `/v1/tiktok/search/hashtags`, `/v1/tiktok/search/suggestions`, and `/v1/tiktok/shop/products/search`.

`SOCIALFETCH_API_KEY` was not set in this session. Those routes were not called live. A missing key returns `api_key_missing` and does not open a socket.

The Bluesky catalog at `https://www.socialfetch.dev/llms-bluesky.txt` lists three routes: `GET /v1/bluesky/posts`, `GET /v1/bluesky/profiles/{handle}`, and `GET /v1/bluesky/profiles/{handle}/posts`. Each successful lookup is documented at 1 credit, and the page names `meta.creditsCharged` as the authoritative billed amount. Those three routes are wired. Bluesky is not left as download-only.

Tool results copy `meta.creditsCharged` when the response includes it. They do not fill `credits_charged` from a remembered price table. The TikTok catalog consulted on this date listed transcript at 1 credit and AI fallback as an extra charge only when AI produced text. That catalog number is not written into the result.

## EasyDown

The blueprint named `jentic/jentic-public-apis` path `apis/openapi/easydown.org/main/1.0.0/openapi.json`. A header check against the raw GitHub URL returned 200. A later unauthenticated GET returned 403, so that snapshot was not diffed byte for byte in this session.

The live spec at `https://api.easydown.org/openapi.json` was readable and is what the client uses. It confirms:

- `POST /api/v1/parse`
- `POST /api/v1/platforms/{platform}/parse`
- Body schema `ParseRequest` with `url`, plus a compatibility alias `link`. The client sends `{"url": url}`.
- Auth is `Authorization: Bearer`, not `x-api-key`.
- Platform enum: tiktok, douyin, toutiao, youtube, twitter, instagram, threads, xiaohongshu, bilibili, kuaishou, weibo.
- Success body is `{status, data, msg}`. `data` holds normalized media. The platform route adds `platformData` and `platformDataVersion`.
- Published credit costs: 1 by default, YouTube 3, Threads 2, Kuaishou 2, Xiaohongshu 10. Failures, unsupported URLs, and auth errors are not charged. The JSON response does not include a billed-credit field, so `credits_charged` stays 0 for EasyDown rather than inventing a number.

`EASYDOWN_API_KEY` was not set. EasyDown was not called live.

## Routing choice

The pasted Phase 2 else-if would call `Client.resource` first whenever social-fetch recognizes the domain. For TikTok that would skip the structured Social Fetch and EasyDown payloads. `research_mcp/util/platform_owners.py` is the source of truth. It tries Social Fetch REST, then EasyDown, then the local library, and records a missing key as an error instead of crashing. A platform with no backend returns `unsupported_platform`.

## Omniget

`tonhowtf/omniget` was not copied. `PLATFORM-OWNERS.md` in that repo is an opt-out notice for site owners, not a backend table. The routing manifest in this repo is the substitute. CI was adapted only as a shape: unit tests on push and pull request, integration on manual dispatch. Rust, frontend, Weblate, and release pipelines were not imported. This change does not create a version tag and does not deploy.

## Remainder checks

The installed `Client.download(url, *, wait=False, timeout=900)` returns a job dict from `jobs.submit` or `wait`. It does not return a file path. `Client.export(job_id, out)` is still required, so auto-export is not redundant. `resource(url, *, archive=False, max_bytes=20971520, timeout=60)` and `account(url, *, count=5)` match the installed source. The default account count in this layer stays 3, which the signature accepts.

`FootageSearch.from_env` is a classmethod and does not take a source argument. `search()` does take `source`. `search_posts` uses that argument. `search_videos` still passes `source="tiktok"`.

The installed FastMCP constructor accepted the existing `host`, `port`, `stateless_http`, and `json_response` arguments. They were not changed. Importing the server succeeded.

`search_videos` still raises `ValueError` on an empty query. Swallowing that exception would change the existing contract, so it was left alone.

EasyDown's live OpenAPI enum includes threads, douyin, bilibili, weibo, kuaishou, xiaohongshu, and toutiao. Their resolver entries stay. Metadata for those seven goes to EasyDown, then fails with a typed error if the key is missing. They are not download-only and they are not dead routes.

Adrian OS exists as a separate product, `emzylavish-art/adrians-mind-command-os`. This branch does not register with it. No deploy and no release tag were created.

## Not done here

No Vercel deploy was made. No live transcript, comment, or download proof exists for a public URL in this session.

## Keys, 2026-11-15

Social Fetch offers a free account at https://app.socialfetch.dev/signup with 100 credits and no card. EasyDown's developer post says new accounts receive 10 trial credits, and its pricing page says signup credits exist. Tokens are created in the dashboard after sign-in. Neither site published a key without an account login. This session has no email touchpoint, and the browser GitHub login for Social Fetch asked for a password that is not available here. No key was created, so no GitHub secret was set and no key value was written to the repository. EasyDown code stays, because a free trial path is documented. Non-TikTok rich metadata still returns a typed missing-key error until EASYDOWN_API_KEY exists.

## Four extra free modules, 2026-11-15

LinkedIn guest HTML for https://www.linkedin.com/in/williamhgates returned HTTP 200 and `og:title`. It was not dead. `linkedin_free.py` makes one request and treats 429 and 999 as terminal. Follower count was not in that meta title, so it stays null.

The installed social-fetch package has no Nitrograph Pinterest endpoint. `pinterest_download` calls `https://www.pinterest.com/resource/PinResource/get/`. A fake pin id returned JSON 404 from that endpoint, which proves the route answers. A search page did not expose a live pin id. `pinterest_free.py` wraps PinResource and falls back to `Client.resource`.

`https://rumble.com/` returned HTTP 403 and a Cloudflare challenge. `rumble_free.py` still exists. It reads `Client.resource` and returns `blocked` instead of a made-up view count.

`https://api.odysee.com/api/v1/proxy` returned 404. `https://api.na-backend.odysee.com/api/v1/proxy` resolved a claim and `claim_search` returned a title. The observed meta keys had no view count. `odysee_free.py` records that gap and does not invent one.


## Live free-source audit, 2026-11-15

omkarcloud/tiktok-scraper was cloned and its parser tests passed, 79 tests. A live video lookup returned play_count, like_count, comment_count, share_count, and MP4 play links. A live profile lookup returned follower_count. The wrapper is `tiktok_free.py`. It imports that checkout only when `TIKTOK_SCRAPER_HOME` points at it. It does not invent counts when the checkout is absent.

Instaloader 4.16 profile fetch redirected to login and the web profile JSON returned HTTP 429. No follower count was observed. One public post shortcode returned a caption and an image URL. `instagram_free.py` is not created, because the profile capability in the blueprint was not verified and a post-only stub would overclaim it.

`https://returnyoutubedislikeapi.com/votes?videoId=jNQXAC9IVRw` returned HTTP 200 JSON with likes and dislikes. `youtube_free.py` wraps that counts endpoint only.

TikTok oEmbed returned HTTP 200 without title, author, cover, or duration. `open-api.tiktokapis.com` did not resolve. `tiktok_oembed.py` was not created.

Reddit `.json` returned HTTP 403. `reddit_free.py` was not created. The existing social-fetch Reddit domain is unchanged because this audit did not re-test that library path.

The published `scraperx` package is a generic SDK, not a platform client. `prezis/scraperx` was not run. `scraperx_free.py` was not created.

The isolated audit could not import `social_fetch`. The parent environment does have it, and it already recognizes Pinterest and LinkedIn. EasyDown's live OpenAPI does not list LinkedIn, Pinterest, Rumble, Odysee, or Telegram.
