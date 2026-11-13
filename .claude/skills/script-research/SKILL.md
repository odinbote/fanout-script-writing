---
name: script-research
description: Gather evidence for a Fanout ad script - transcribe competitor video ads from the Meta Ad Library, find YouTube videos that beat their channel's normal views, and collect pain points with engagement numbers from Hacker News, Reddit (archive) and Stack Exchange. Use when asked to research a topic, find pain points, transcribe an ad, or break down a tonality reference.
---

# Script research

Finds what engineers are already saying and what competitors already pay to say, so a script is built from real
words. Full method notes, URLs and limits: `docs/04-research-methods.md`.

## The three sources, used together

1. **Competitor video ads** (Meta Ad Library in the built-in browser, then OpenRouter `analyze_video` with
   `google/gemini-2.5-flash`). Look for ads running 60+ days or with several versions. Transcribe them. Note the
   pain each one opens on and the order of its beats.
2. **Organic outliers** (YouTube via `yt-dlp`): views divided by the channel's median for the same format.
   Record the opening lines of the outliers.
3. **Communities**: Hacker News (Algolia API), Reddit through the Arctic Shift archive only, Stack Exchange,
   newsletters. For each pain: a short quote in the person's own words, the link, the engagement number.

Never rely on one source. Reddit alone was rejected.

## A wide sweep with the pipeline

When the owner asks for fresh material across everything rather than one topic:

```bash
bin/pipeline doctor     # what is switched on
bin/pipeline collect    # 20 to 40 minutes on the free route; run it in the background
bin/pipeline enrich     # transcripts, ad copy and top comments for the leaders
bin/pipeline pack       # evidence packs in output/<date>/evidence/
```

For competitors in `[ads].competitors`, read each advertiser's Ad Library page sorted by impressions in the
built-in browser, save the page text to `data/raw/adlibrary_pages/<date>/<slug>.txt`, and run
`bin/pipeline import-adlibrary` on it. Report the top three per method with their grade ("Long-Runner, 98 days,
25 versions"; "outlier, 12x the channel's median"). Never print key values from `.env`.

## A tonality reference

When the owner sends an Ad Library link for tone:

1. Open `https://www.facebook.com/ads/library/?active_status=all&ad_type=all&country=ALL&id=<id>&media_type=all`.
2. Read the advertiser, start date, versions and the video `src` from the page.
3. Transcribe with `analyze_video`. Ask for the verbatim transcript, the main captions only, delivery, the
   structure beat by beat, and five phrases or sentence shapes that give it its voice.
4. Save to `research/reference-ads/<creator>-<brand>.md`.

## Output

- `research/<date>-<topic>/competitor-ads-transcribed.md`
- `research/<date>-<topic>/organic-video-evidence.md`
- `research/<date>-<topic>/pain-points-by-topic.md`

Each file ends with what it means for the script: which pain is strongest and the exact everyday phrases people use.

## Rules

- Do not call Reddit's own API and do not spoof a browser user agent. Use the archive.
- Do not download videos. Captions, metadata and transcripts only.
- Quote engagement numbers only when the page or API shows them. Mark anything unverified.
- Keep quotes short. Link to the source.
- Signed ad video URLs expire: transcribe in the same session.
- When sending anything to an outside model, leave out the owner's name and contact details.
- Research can run alongside drafting. Do not hold a first draft back for it.
