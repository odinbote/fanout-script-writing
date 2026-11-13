# Fanout script writing: standing instructions

This repo is for writing Fanout's UGC ad scripts. Nothing else happens here: no video generation, no editing.

## Before writing anything

Read `docs/01-framework.md` and `docs/02-rules.md`. Use the `script-writer` skill for scripts and the
`script-research` skill for evidence.

## The rules that matter most

1. Follow the six beats in `docs/01-framework.md`. The wording there is the owner's own.
2. Every line must make sense to a normal person hearing it once. Explain a term in the same sentence.
3. Normal words, full sentences, one storyline. No fragments, no sayings, no quiz of jargon.
4. Value first: the five things to learn. Fanout is named once, at the end.
5. Never name a competitor. Product claims only from `docs/product-facts.md`. No results promises.
6. Copy the tonality reference the owner sends. Transcribe it first.
7. Pain points come from competitor ads, organic videos and communities together.
8. Run `python3 tools/check_script.py` on every script.

## Working with the owner

- Replies are short: the script, two or three lines, the file link. Details go in files.
- Show one version. Alternates go in the script's sources file.
- When feedback comes, change only what was asked. When the owner dictates wording, use it.
- A new rule from feedback goes into `docs/02-rules.md` straight away.

## Files

- Finished scripts: `scripts/final/<name>.txt` plus `<name> - sources.md`.
- Research: `research/<date>-<topic>/`. Tonality references: `research/reference-ads/`.
- Local only, git-ignored, never to be committed: `research/`, `scripts/archive/`, every `- sources.md` file,
  `docs/05-draft-history-*.md`, `config/fanout.local.toml`, `data/`, `output/`, `.env`. This repo is public.
- The sourcing pipeline is `bin/pipeline` (see the README). Its database and `output/` are local and git-ignored.
- Never create shortcuts, aliases or symlinks.
- A script picked for production is copied to `~/Documents/fanout/AI ugc/<script name>/script.txt`. Generated
  videos never go in this repo.

## Money and publishing

- Ask before any paid generation. Transcribing an ad or a cold read costs a fraction of a cent and needs no ask.
- Commit after each approved script. Push only when the owner asks. Before any push, check that nothing from
  the local-only list is staged and that no competitor is named in a tracked file.
- When sending text to an outside model, leave out the owner's name and contact details, and swap the brand name
  for a placeholder in cold reads.
