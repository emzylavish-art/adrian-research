# Source notes

Saved 2026-11-15 so later edits do not depend on a search snippet.

## EasyDown

- Docs: https://easydown.org/docs/en
- Quick start: https://easydown.org/docs/en/quick-start
- Live OpenAPI: https://api.easydown.org/openapi.json
- Named Jentic path: https://github.com/jentic/jentic-public-apis/tree/main/apis/openapi/easydown.org/main/1.0.0/openapi.json
- Routes: POST /api/v1/parse and POST /api/v1/platforms/{platform}/parse
- Body: {"url": "<public media url>"}. Compatibility alias is link.
- Auth: Authorization: Bearer
- Platform enum: tiktok, douyin, toutiao, youtube, twitter, instagram, threads, xiaohongshu, bilibili, kuaishou, weibo
- Credits published on the operation: 1 default, YouTube 3, Threads 2, Kuaishou 2, Xiaohongshu 10. The JSON body does not include a billed-credit field.

## Social Fetch

- TikTok catalog: https://www.socialfetch.dev/llms-tiktok.txt
- Bluesky catalog: https://www.socialfetch.dev/llms-bluesky.txt
- Bluesky post: https://www.socialfetch.dev/docs/api/v1/bluesky/posts/get.mdx
- Bluesky profile: https://www.socialfetch.dev/docs/api/v1/bluesky/profiles/handle/get.mdx
- Errors: https://www.socialfetch.dev/docs/errors.mdx
- Auth: x-api-key
- Free smoke test: GET https://api.socialfetch.dev/v1/whoami
- Authoritative billed amount: meta.creditsCharged
- Bluesky routes that exist: GET /v1/bluesky/posts, GET /v1/bluesky/profiles/{handle}, GET /v1/bluesky/profiles/{handle}/posts
- Next TikTok routes appended from the 2026-11-15 catalog: /v1/tiktok/search, /v1/tiktok/search/top, /v1/tiktok/users/search, /v1/tiktok/profiles/{handle}/followers, /following, /region, /audience, /engagement, /live, /v1/tiktok/live, /v1/tiktok/videos/download, /v1/tiktok/collections/videos, /v1/tiktok/songs, /v1/tiktok/music/{clipId}/videos, /v1/tiktok/shop/products, /v1/tiktok/products, /v1/tiktok/products/reviews, /v1/tiktok/profiles/{handle}/showcase-products, /v1/tiktok/ad-library/ads, /v1/tiktok/ad-library/ads/search. Audience is catalogued at 30 credits, engagement at 5, hosted download at 11 when media is returned.

## social-fetch library

- Repository: https://github.com/Karnaf0katom/social-fetch
- Client.download(url, wait=False, timeout=900) returns a job dict. It does not return a file path. Client.export writes the file and checks sha256.
- FootageSearch.from_env is a classmethod. search() accepts source.

## Omniget

- PLATFORM-OWNERS.md: https://raw.githubusercontent.com/tonhowtf/omniget/main/PLATFORM-OWNERS.md
- That file is an opt-out notice, not a routing table.
- CI shape: https://raw.githubusercontent.com/tonhowtf/omniget/main/.github/workflows/ci.yml
