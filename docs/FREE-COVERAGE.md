# Free-path coverage matrix

Smoked 2026-11-15 with `SOCIALFETCH_API_KEY` and `EASYDOWN_API_KEY` unset. `credits_charged` was 0 on every free path. A cell says what that call returned. It does not invent a number, and a catalog price is not a billed amount.

| Path | URL | path_used | source_detail | Typed errors |
| --- | --- | --- | --- | --- |
| LinkedIn guest HTML | `https://www.linkedin.com/in/williamhgates` | free | linkedin-guest | `rate_limited` |
| Pinterest PinResource | `https://www.pinterest.com/pin/16466354885769312/` | free | pinterest-pinresource | `missing_field` title |
| Rumble resource | `https://rumble.com/v1.html` | free | rumble-resource | `blocked` |
| Odysee proxy | `lbry://@3ctech#0/Odysee#288` | free | odysee-proxy | `missing_field` view count |
| TikTok scraper | `https://www.tiktok.com/@tiktok/video/7692114317151423775` | free | omkarcloud-tiktok | none |
| YouTube free | `https://www.youtube.com/watch?v=jNQXAC9IVRw` | free | youtube-oembed-page+returnyoutubedislike | `api_key_missing` for EasyDown |

The LinkedIn row is this smoke. An earlier call the same day, before LinkedIn answered 429, returned the name and left followers null. Followers stay null even on a successful guest parse.

## Fields

`returned` means the normalized `get_post` or `get_profile` field was filled. `null` means it stayed empty on that call.

| Field | LinkedIn | Pinterest | Rumble | Odysee | TikTok | YouTube |
| --- | --- | --- | --- | --- | --- | --- |
| title | null | null | null | returned | null | returned |
| description | null | blank space | null | returned | returned | null |
| author.username | null | returned | null | returned | returned | returned |
| author.display_name | null | returned | null | returned | returned | returned |
| author.bio | null | null | null | null | returned | null |
| author.followers | null | null | null | null | returned | null |
| author.verified | null | null | null | null | returned | null |
| author.avatar_url | null | null | null | null | returned | null |
| author.profile_url | null | null | null | null | returned | returned |
| created_at | null | null | null | null | returned | null |
| metrics.views | null | null | null | null | returned | returned |
| metrics.likes | null | null | null | null | returned | returned |
| metrics.dislikes | null | null | null | null | null | returned |
| metrics.comments | null | null | null | null | returned | null |
| metrics.shares | null | null | null | null | returned | null |
| metrics.saves | null | null | null | null | returned | null |
| metrics.reposts | null | null | null | null | returned | null |
| media.thumbnail_url | null | returned | null | null | returned | null |
| media.video_urls | null | null | null | null | returned | null |
| media.image_urls | null | returned | null | null | null | null |
| media.audio_urls | null | null | null | null | null | null |
| media.duration_ms | null | null | null | null | returned | null |
| media.width | null | null | null | null | returned | null |
| media.height | null | null | null | null | returned | null |
| transcript | null | null | null | null | null | null |
| comments_preview | null | null | null | null | null | null |
| hashtags | null | null | null | null | null | null |
| music | null | null | null | null | null | null |
| location | null | null | null | null | null | null |
| is_ad | null | null | null | null | null | null |

Observed TikTok values on that URL: views 563700, likes 19700, comments 3915, shares 1469, saves 1703, reposts 0, followers 96800000, created date `2026-10-02T16:52:37Z`, duration 65 seconds, width 720, height 1280, one play link. Title was null in the scraper payload, not only in the schema.

YouTube free path, observed with `EASYDOWN_API_KEY` absent: title `Me at the zoo`, author `jawed`, profile `https://www.youtube.com/@jawed`, views 448669298, likes 20139871, dislikes 452591. `path_used` was `free`, `source_detail` was `youtube-oembed-page+returnyoutubedislike`, credits were 0. Title and author come from public YouTube oEmbed. Views come from the public watch page. Counts come from `returnyoutubedislike`. Created date, description, transcript, and media stayed null. A present EasyDown key keeps the paid lookup and does not call these free sources.

## Not mapped, not absent

The TikTok scraper payload for that video also had `music`, `mentions`, an `is_ad` bool, and a `download_link`. `get_post` left music, mentions, and `is_ad` null because the wrapper does not copy them. The download link is not added to `media.video_urls`; that list has the play link only. Hashtags, images, and location were empty in the scraper payload.

Pinterest board name is in `raw_platform_data`. It is not a schema field.

## Paid gaps

No free module returned these. A missing key returns a typed error and does not invent the payload.

| Gap | Free result | Paid path | Gate |
| --- | --- | --- | --- |
| Transcript | null on every smoked path | `get_transcript` calls Social Fetch `GET /v1/tiktok/videos/transcript` | TikTok only. `SOCIALFETCH_API_KEY`. Other platforms return `unsupported_content`. |
| Shop | no free shop reader | `search_shop_products` calls `GET /v1/tiktok/shop/products/search`. Store, product, review, and showcase tools use the same key. | TikTok only. Missing key returns `api_key_missing` and an empty result list. |
| Audience | no free audience reader | `get_tiktok_audience` calls the Social Fetch audience route | Does not run unless `confirm=True`. Catalog lists 30 credits. `credits_charged` still comes from the response. |
| Hosted media | no hosted file | `get_tiktok_hosted_media` asks Social Fetch to host a TikTok file | Does not run unless `confirm=True`. Catalog lists 11 credits when a file is returned and 1 when it is not. The free TikTok play link is not this tool, and it is not `download_media`. |

Engagement is the same shape as audience: no free source, `confirm=True`, catalog lists 5 credits, billed amount comes from the response. Follower and following lists are also Social Fetch key paths. EasyDown rich metadata for YouTube title, author, views, and media remains paid and was not called in this smoke.
