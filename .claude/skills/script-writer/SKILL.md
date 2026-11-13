---
name: script-writer
description: Write a Fanout UGC ad script on the approved six-beat framework ("sauce" hook, the research, what to learn, five things, Fanout once at the end, tagline). Use when asked to write, rewrite or re-voice a script for Fanout or for one Fanout course, or to apply a tonality reference ad to a script.
---

# Script writer

Writes one Fanout UGC ad script the way the owner approved on Nov 12, 2026.

## Read first

1. `docs/01-framework.md`: the six beats, how to write the five things, the two finished scripts.
2. `docs/02-rules.md`: the rules and the lines that were rejected.
3. `docs/product-facts.md`: the only claims a script may make.

`references/craft.md` in this folder has hook archetypes and line tests. Use it for alternates. Where it disagrees
with the framework or the rules, the framework and the rules win.

## Steps

1. **Get the brief.** Topic or course, tonality reference (an Ad Library link), the message (winning static or
   tagline), any fixed wording. If something is missing, write with what there is.
2. **Get the five things.** Re-read the course page on fanout.sh (pages listed in `docs/product-facts.md`), group
   its modules into five, and order them the way someone would learn them.
3. **Fill the six beats** using the template in `docs/01-framework.md`. Give each of the five things one plain
   clause ("That's how…", "which is…", "meaning…", "for example: …").
4. **Apply the tonality reference** if there is one. Transcribe it (`docs/04-research-methods.md`, section 1), save
   it to `research/reference-ads/`, pick five of its phrases or sentence shapes and re-voice the beats with them.
   Keep the beats and the five things unchanged.
5. **Stranger test.** Read each line as someone who has never heard of Fanout or the field. Fix any line that
   needs prior knowledge.
6. **Cold read.** Give the script, brand name replaced by a placeholder, to an outside model playing an engineer
   who hears it once. Ask what the site is, who it is for, what you get, which lines confused them, which sound
   like an ad, and whether they would tap. Rewrite what it could not picture.
7. **Check.** `python3 tools/check_script.py "scripts/final/<name>.txt"`. No competitor names, no sentence over
   24 words, 120 to 160 words.
8. **Save.** `scripts/final/<name>.txt` (spoken lines only, one beat per paragraph) and
   `scripts/final/<name> - sources.md` (where each line came from, the tonality reference, alternates).
9. **Show it.** The script in the reply, two or three lines on what changed, the file link. One version.

## Do not

- Name a competitor, promise results, or claim numbers that are not in the product facts.
- Put a Fanout feature line in every beat. Fanout is named once, at the end.
- Write fragments, sayings, or a quiz of technical terms.
- Add back what the owner cut: a "my manager said…" opening, "the first lessons are free", "the link's right here".
- Start video generation. That is a separate workflow and needs the owner's yes each time.

## When feedback comes

Change only what was asked. If the owner dictates wording, use it. If the feedback is a new rule, add it to
`docs/02-rules.md` and, if it changes the beats, to `docs/01-framework.md`.
