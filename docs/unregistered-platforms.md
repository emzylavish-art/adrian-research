# Unregistered platforms

Adrian OS is not a platform in this server and it must stay that way. It is a separate product, `emzylavish-art/adrians-mind-command-os`. Do not register it here, do not add a client entry for it, do not import its modules, do not add an environment variable that points at it, and do not deploy this server into it from this repository. The same exclusion covers Grokbot and Google Sheets. Those names are not URL platforms and they are not MCP registrations for this repo.

This file is the list of what this server also refuses to treat as a registered owner. A host can be detected and still be unregistered. Detection only chooses a route. It does not create a new product integration.

URL hosts with no dedicated Social Fetch REST owner and no EasyDown parse route are unregistered for structured metadata. The local library can still search or download some of them. Those hosts are Pinterest, Twitch, Snapchat, LinkedIn, Mastodon, Facebook, and Reddit. Facebook and Reddit stay on the library path. Reddit comments and native images stay library-only. Do not invent REST routes for them.

Any host that is not in `research_mcp/util/urls.py` is unregistered. `get_post` returns `unsupported_platform` and does not guess a backend. Do not add Adrian OS, a private app host, or an internal dashboard host to that table to make a call succeed.

EasyDown's live platform enum is the registered parse list: TikTok, Douyin, Toutiao, YouTube, Twitter/X, Instagram, Threads, Xiaohongshu, Bilibili, Kuaishou, and Weibo. Social Fetch REST in this server is registered only for the routes named in `docs/source-notes.md`. A new platform is unregistered until that note and `research_mcp/util/platform_owners.py` both name the real route.
