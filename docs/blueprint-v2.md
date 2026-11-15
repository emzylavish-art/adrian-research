# Closing remainder

This file is the final pasted remainder, not a rebuild prompt. The resolutions are in AUDIT.md. Do not rebuild research_mcp/server.py from it.

Everything left, in one block. Social Fetch REST credit costs — I quoted one credit base, ten for media download, five for engagement, thirty for audience, two per hosted file. Those numbers are from Social Fetch’s public pricing page as I understood it, not a live lookup. Pull the real pricing before surfacing credits_charged.
Social-fetch Client method signatures — download, resource, account, download_image, status, export. Parameter names and return shapes may differ from what I assumed. The audit must read the actual source or docs and correct the tool code accordingly.
FootageSearch.from_env — I assumed it accepts a source parameter. It might not. It might be a classmethod that reads env vars for API keys. Test it. If no source param exists, search_posts cross-platform routing needs a different approach.
social-fetch install URL — git+https://github.com/Karnaf0katom/social-fetch.git. That username and repo are from my training, not verified. If pip install fails, the audit finds the correct source. Do not hardcode a wrong URL into requirements.txt.
FastMCP API — mcp>=1.9,<2. The FastMCP constructor args I used — host, port, stateless_http, json_response — match recent versions but the exact signature may have shifted. If server.py fails to construct, check the installed version’s docs.
Existing search_videos error handling — the blueprint says harden it to return empty list on exception. That changes behavior from raising. Confirm that’s intended before merging, since any consumer expecting an exception will break silently.
Threads, Douyin, Bilibili, Weibo, Kuaishou, Xiaohongshu, Toutiao — seven platforms added to RESOLVERS but only TikTok got explicit tool routing. For those seven, the only path is EasyDown. If EasyDown’s openapi shows they lack a /platforms/{name}/parse route, those seven RESOLVER entries should be removed or marked download-only. Dead routes produce confusing errors.
Bluesky — flagged as priority but no Bluesky-specific REST endpoints were named because Social Fetch’s public docs may not list them. The audit checks whether api.socialfetch.dev/v1/bluesky exists. If not, Bluesky stays download-and-resource only.
Adrian OS — referenced as the consumer system. If it doesn’t exist yet or has a different name or MCP registration format, Phase 8’s instructions are wrong. The audit or you should confirm what Adrian OS actually is before Phase 8 starts.
Test runner — no pytest or unittest declaration. Default to pytest. Add pytest to requirements.txt.
Port 8765 — assumed free. If something else binds it, the HTTP mode fails. Document that PORT is overridable, which it is via env var, so this is minor but worth one line in the README.
The normalize function in section 1.2 had garbled syntax in places — lines with bare variable references instead of assignments. Manus must rewrite it cleanly rather than copying it verbatim. Same for the RESOLVERS regex entries that contained spaces inside character classes or pattern bodies — those won’t compile. Rewrite every regex from the pattern intent, not the literal text.
api_get header logic — socialfetch uses x-api-key, EasyDown assumed Bearer. The openapi.json will show EasyDown’s real auth scheme. Use that. Don’t assume Bearer.
download_video auto-export — the blueprint says auto-export when output_dir is given and status is ready. If _client.download with wait=True already returns the file path, the export call may be redundant. The audit checks whether download’s return includes a local path.
Feature branch name — v1 blueprint said feature/full-tiktok-layer, v2 said feature/universal-social-layer. Manus uses feature/universal-social-layer. The v1 name is obsolete.
That’s the complete remainder. Nothing held back.
