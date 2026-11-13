# Research methods

What was actually used on Nov 12, 2026, what it costs and where it breaks.

Research output (transcripts, quotes, evidence packs) is saved under `research/`, which stays on the owner's
machine and is not in git.

## 1. Competitor video ads (Meta Ad Library, transcribed)

No login or key is needed. Use the built-in browser.

**Find ads**

- Keyword search, video only, sorted by impressions:
  `https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=ALL&q=<keyword>&search_type=keyword_exact_phrase&media_type=video&sort_data[mode]=total_impressions&sort_data[direction]=desc`
- One ad by its Library ID (use `active_status=all`, or stopped ads come back as "no ads match"):
  `https://www.facebook.com/ads/library/?active_status=all&ad_type=all&country=ALL&id=<library id>&media_type=all`
- Keywords that returned our niche: `system design`, `AI engineer`. `"senior engineer"` and
  `math machine learning` are mostly noise; filter by advertiser.

**What to read off each card**

- "Started running on …": days running. 60+ days means they keep paying for it.
- "N ads use this creative and text": they are scaling that creative.
- The ad copy, the length of the video, and the `<video>` element's `src` (read it from the page).

**Transcribe**

- OpenRouter MCP `analyze_video` with the video's `src` as `video_path` and `model: google/gemini-2.5-flash`.
- Pass the model explicitly. Six calls at once failed with a 400; one to three at a time worked.
- The video URLs are signed and expire. Transcribe in the same session you found them.
- Ask for: a verbatim transcript with rough timestamps, only the five or six main captions, format and tone in
  two lines, and "do not invent words you cannot hear". Without the caption limit, a screen-recording ad returns
  hundreds of lines of on-screen text.
- For a tonality reference also ask for delivery (pace, energy, filler words, how sentences start) and five
  phrases or sentence shapes that give it its voice.
- Cost is a fraction of a cent per ad.

**What it found:** `research/2026-11-12-senior-engineer/competitor-ads-transcribed.md`.

## 2. Organic outliers (YouTube)

- `yt-dlp` with `ytsearchN:` queries and `--dump-json --skip-download` for view counts.
- For each candidate, fetch the channel's recent uploads in the same format (Shorts or long) and compute
  views ÷ channel median. 3x and above is an outlier.
- Pull auto-captions (`--write-auto-subs --skip-download`) for the opening lines. No video downloads.
- Throw out paid-traffic anomalies: millions of views with a few hundred likes.
- TikTok and Instagram have no free route with trustworthy numbers.

**What it found:** `research/2026-11-12-senior-engineer/organic-video-evidence.md`. The patterns among the outliers:
a long struggle handed back short ("It took me 10+ years to realize what I'll tell you in 8 minutes"),
wrong order and wasted months as the pain, and the junior-to-senior gap named in line one followed by a numbered list.

## 3. Community pain points

- **Hacker News**: `https://hn.algolia.com/api/v1/search?query=<q>&tags=story&hitsPerPage=30` gives points and
  comment counts; `https://hn.algolia.com/api/v1/items/<id>` gives the thread.
- **Reddit, through the Arctic Shift archive only**:
  `https://arctic-shift.photon-reddit.com/api/posts/search?subreddit=<sub>&title=<word>&after=2025-01-01&limit=100&fields=id,title,score,num_comments,subreddit,created_utc,selftext`
  and `…/api/comments/tree?link_id=t3_<id>&limit=300`. It is slow; use long timeouts. Scores are snapshots and run
  lower than live. Reddit's own API returns 403 to scripts: do not call it and do not spoof a browser user agent.
- **Stack Exchange**: `https://api.stackexchange.com/2.3/search/advanced?order=desc&sort=votes&q=<q>&site=<site>`
  (gzip; use `curl --compressed`). Mostly older questions.
- **Newsletters and blogs**: web search. Quote likes only when the page shows them.
- **X and LinkedIn**: no free route that shows engagement numbers. Nothing from them was used.

Each pain needs a short quote in the person's own words, the link and the engagement number.

**What it found:** `research/2026-11-12-senior-engineer/pain-points-by-topic.md` (ten topics).

## 4. Product facts

Read the course pages on fanout.sh directly: `/system/overview`, `/ml-math/overview`, `/ai/overview`,
`/inference-eng`, `/ai-engineering/overview`, `/roadmaps`, and the homepage. Summary in `docs/product-facts.md`.

## 5. Script craft

Sources read on Nov 12 for how to write and how to get a model to write better:

- Direct-response order for UGC ads (Hook, Problem, Solution, Value props, Proof, CTA; "I had a problem, I tried
  this, here's the result"): https://motionapp.com/blog/how-to-write-ugc-ad-scripts
- Setup, tension, payoff per segment, and using a model for the skeleton rather than the voice (George Blackman):
  https://vidpros.com/insiders/george-blackman-youtube-scriptwriting/
- The stranger test ("mark every moment that would make sense to a stranger with zero context"; add missing
  context in one clause): https://t.me/s/ShortFormNotes?before=11
- Hook, body and plug craft adapted from four MIT-licensed skill sets: `.claude/skills/script-writer/references/craft.md`.

## 6. The sourcing pipeline (`bin/pipeline`)

For a wide sweep instead of a targeted search. It pulls from the same sources (plus pasted Amazon reviews),
stores everything in `data/pipeline.db`, and ranks:

- **Ads**: 60+ days running is a Long-Runner, 30 to 59 a Performer; more versions of one creative means scaling.
- **Organic**: views ÷ the channel's median for the same format; 10x is a mega outlier, 3x an outlier.
- **Community**: engagement percentile within the platform, boosted by pain words and topic words from the config.

`bin/pipeline run` writes evidence packs to `output/<date>/evidence/` with codes (A1, O2, C8). The first run's
packs are kept in `research/2026-11-11-first-run/`. `collect` takes 20 to 40 minutes on the free route.
It does not transcribe ad videos: do that with section 1.

## Limits to remember

- Ad Library transcripts need the OpenRouter MCP to be connected (Google models only on the current key).
- The cold read sends the script to an outside model. Swap the brand name for a placeholder first.
- The swipe-file database and `output/` are local only. A fresh clone starts with an empty swipe file.
