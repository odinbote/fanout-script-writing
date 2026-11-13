# Fanout script writing

Everything used to write Fanout's UGC ad scripts: the approved framework, the rules, the process from brief to
finished script, the research behind it, the finished scripts, and the Claude Code skills that do the writing.

## Start here

| If you want to… | Open |
|---|---|
| Write a new script | `docs/01-framework.md` (the six beats and a fill-in template) |
| Know what gets a script rejected | `docs/02-rules.md` |
| See the whole process, brief to file | `docs/03-process.md` |
| Research a topic or transcribe an ad | `docs/04-research-methods.md` |
| Check what a script may claim | `docs/product-facts.md` |

## The framework in one look

1. "I'm about to reveal some sauce for engineers that's not out there. This is all you need to know to actually become a **[role]**."
2. "I searched YouTube. I read a bunch of blogs. I even asked a few **[role]s**."
3. "And I found out what you actually need to learn."
4. Five numbered things, each explained in one plain clause.
5. "And you can find all of these only on Fanout."
6. "Curated, mapped & complete."

## Using it with Claude Code

Open Claude Code in this folder. Two skills load from `.claude/skills/`:

- **script-writer**: "write a script for the System Design course", "re-voice this script like this ad: <Ad Library link>".
- **script-research**: "find pain points for inference engineering", "transcribe this ad: <Ad Library link>".

`CLAUDE.md` holds the standing rules for any session here.

## Check a script

```bash
python3 tools/check_script.py "scripts/final/everything you need to become a senior engineer.txt"
```

Words, spoken seconds, the Veo clip plan and cost, competitor names, over-long sentences.

## The sourcing pipeline

Built on Nov 11, 2026. It collects competitor ads, organic videos and community posts, ranks them and writes
evidence packs. Python standard library only (needs Python 3.11+; `bin/pipeline` uses Homebrew's 3.14).

```bash
bin/pipeline doctor                        # which sources and keys are on
bin/pipeline run                           # collect -> enrich -> rank -> pack
bin/pipeline collect --pillar community    # one method: ads, organic, community, marketplace
bin/pipeline show --pillar organic         # ranked table
bin/pipeline import-adlibrary FILE.txt     # an advertiser's Ad Library page text
bin/pipeline pack                          # evidence packs in output/<date>/evidence/
bin/pipeline check SCRIPT.txt --source A1  # overlap between a script and a source item
```

Keys are optional and go in `.env` (template: `.env.example`). Tests: `python3.14 -m unittest discover -s tests`.
Copy `config/fanout.local.example.toml` to `config/fanout.local.toml` and fill in the names you track.
The swipe file (`data/pipeline.db`) and `output/` stay on your machine and are not in git.

## What is in here

```
docs/                  framework, rules, process, research methods, product facts
scripts/final/         approved scripts
.claude/skills/        script-writer and script-research
tools/check_script.py  the script checker
pipeline/, bin/, tests/ the sourcing pipeline (collect, rank, pack, check)
config/fanout.toml     product facts and where to look
```

Kept on the owner's machine and not in git: `research/` (ad transcripts, quotes, evidence packs), each script's
sources file, older drafts, `config/fanout.local.toml` (names of competitors, channels and products; template in
`config/fanout.local.example.toml`), `data/` and `output/`.

## Finished scripts

- `scripts/final/everything you need to become a senior engineer.txt`
- `scripts/final/all you need to become an AI engineer.txt`

## Not part of this repo

Video generation and editing are separate workflows and are not part of this repo.
