# Process, A to Z

How a script goes from a brief to a file the video pipeline can use.

## A. What the owner gives

1. **The topic or course**: a pain point ("how you become a senior engineer") or one course ("AI Engineering").
2. **A tonality reference**: a Meta Ad Library link to a UGC ad whose voice should be copied.
3. **The message**: usually a winning static ad or the tagline.
4. Anything fixed: a hook line, an ending, words to use.

If one of these is missing, write on the framework with what there is. Do not hold the script up for it.

## B. Product facts

Open the course's page on fanout.sh (list in `docs/product-facts.md`) and read the module and lesson list.
The five things in the script come from there. Add anything new to `docs/product-facts.md`.

## C. Research

Methods, URLs and costs are in `docs/04-research-methods.md`. Three sources, used together:

1. **Competitor video ads** from the Meta Ad Library, transcribed. Long-running ads and ads with many versions
   show which pains and formats competitors keep paying for.
2. **Organic outliers**: YouTube videos far above their own channel's normal views, with their opening lines.
3. **Communities**: Hacker News, Reddit (archive only), Stack Exchange, newsletters. Quotes with engagement numbers.

Save everything to `research/<date>-<topic>/`. Transcribe the tonality reference into `research/reference-ads/`.
`research/` stays on this machine: it is git-ignored.

Research is for choosing the pain and the words. It does not have to finish before the first draft:
write from what is in hand and fold the rest in.

## D. Write

1. Fill the six beats in `docs/01-framework.md`.
2. Pick the five things from the product facts. Give each one plain clause.
3. Apply the tonality reference: five of its phrases or sentence shapes.
4. Check against `docs/02-rules.md`.

## E. Stranger test and cold read

- Read every line as someone who has never heard of Fanout. Fix any line that needs prior knowledge.
- Cold read: give the script to an outside model with the brand name swapped for a placeholder, playing an
  engineer who hears it once. Ask what the site is, who it is for, what you get, which lines confused them, which
  lines sound like an ad, and whether they would tap. Rewrite what it could not picture.

## F. Check

```bash
python3 tools/check_script.py "scripts/final/<name>.txt"
```

It reports words, spoken seconds, the Veo clip plan and cost, competitor names and sentences that are too long.
To measure how close a script sits to a source item: `bin/pipeline check "<script>" --source A1`.

## G. Save

- `scripts/final/<name>.txt`: the spoken lines only, one beat per paragraph.
- `scripts/final/<name> - sources.md`: where each line came from, the tonality reference, alternates. Local only (git-ignored).

Name the file after the script's promise, in plain words.

## H. Show the owner

The script in the reply, two or three lines on what changed, the file link. One version.

## I. Iterate

Expect several rounds. Change only what the feedback asks for. When the owner dictates wording, use their words.
When a rule comes out of the feedback, add it to `docs/02-rules.md`.

## J. Hand off to video

When the owner picks a script for production, copy it to `~/Documents/fanout/AI ugc/<script name>/script.txt`.
Video generation is a separate workflow with its own rules (trial clip first, a yes before every paid
generation). It is not part of this repo.

## K. Commit

Commit after each approved script. Push only when the owner asks.
