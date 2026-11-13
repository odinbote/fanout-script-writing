# Script craft for Fanout UGC

Hook archetypes, the chain-of-hooks body, plug styles and line tests. Written on Nov 11, 2026, before the
approved framework. **Where this file disagrees with `docs/01-framework.md` or `docs/02-rules.md`, those win.**
In particular: the approved hook is the "sauce" line, the body is a numbered list of five things, Fanout is
named once at the end, and the script closes on the tagline. Use this file for alternates and for testing lines.

One test, read out loud: **would a real engineer say this to a friend, and does every line make you want the next one?**

---

## 1. Hooks

### 1.1 Write five, ship one

Write five hooks, each from a different archetype, then judge them with the 5-test bar. Keep the best plus two
alternates for testing. Ten rewordings of one idea are one hook.

### 1.2 Archetypes

| Archetype | Shape | Fanout example |
|---|---|---|
| **Investigator** | "I found [hidden thing] in [familiar place] that [unexpected effect]" | "There's one diagram that explains why Discord moved off Cassandra." |
| **Contrarian** | "Everyone thinks X. That's exactly why Y." | "Everyone grinds coding puzzles for system design rounds. That's why they freeze." |
| **Teacher** | "[Person] did [result] using [unexpected method]" | "Netflix breaks its own servers on purpose. On a schedule." |
| **Experimenter** | "I did X for [time] to find out Y" | Only as a relatable situation, never as a result. |
| **Fortuneteller** | "[Thing] is about to change how [audience] [does action]" | "Inference engineering is the job title you'll see everywhere next year." |
| **Magician** | the visual carries it; the line points at it | "Watch what happens to one request before your Netflix page even loads." |
| **Specific moment** | "You know that moment when [hyper-specific moment]?" | "The interviewer says 'design YouTube' and your mind goes blank." |
| **Confession / gatekeeping** | "I wasn't going to share this, but…" | "I'm about to reveal some sauce for engineers that's not out there." |
| **Warning / loss** | "If you're still [habit], here's what it costs you" | "If you're learning AI from random YouTube videos, you're missing the layer that gets you hired." |
| **Contrast** | "Most [role]s do A. The ones who [result] do B." | "Most engineers memorise architectures. Senior engineers can explain why they break." |

### 1.3 The 5-test bar

1. **Friction**: would an engineer scrolling at full speed stop?
2. **A named trigger**: curiosity gap, identity call-out, pain, contrarian, loss, relatable moment or pattern interrupt.
3. **Complete thought**: it lands on its own.
4. **Real voice**: sounds like a person on camera, not ad copy.
5. **Personal stakes**: it answers "why should I care?".

### 1.4 Moves that sharpen a flat hook

1. Cut the first three words.
2. Add a specific number or name.
3. Name the exact viewer.
4. Name the category of the answer and hold the answer.
5. Swap weak verbs for strong ones.
6. Add a contradiction.

If three of these leave it flat, change the archetype, not the wording.

### 1.5 Hooks that fail

- Brand first: "Fanout is…", "Check out this site…"
- "Hey guys", "so today"
- Vague tease with nothing after it: "this changed everything". A secret-sauce hook works only when the next
  sentence says what the sauce is about.
- A command with no felt cost: "Stop scrolling".
- A stat with no stakes.
- Cleverness that needs decoding. Clarity beats wit.

### 1.6 Three layers

- **Spoken line**: lands inside the first clip.
- **On-screen text**: three to seven words that sharpen the line, never repeat it.
- **Visual note**: what the first frame shows, for the editor.

---

## 2. The body

### 2.1 But / so

Join beats with "but" (a complication) or "so" (a consequence), not "and then". In the approved framework the
research line and the turn do this job: "I searched… **And** I found out what you actually need to learn."

### 2.2 Specific beats generic

Engineers trust specifics: a named system, a number, a moment. One concrete noun per beat. But a specific the
viewer does not know is noise: explain it in the same sentence.

### 2.3 Line tests (run on every sentence)

- **Cut test**: if this line is deleted, does anyone miss it?
- **Pull test**: does this line make me want the next one?
- **Read-aloud test**: say it. Anything that sounds like a brand wrote it gets rewritten in first person.
- **Stranger test**: would someone with zero context understand it on one listen?

---

## 3. The plug

The weak plug is a bolt-on: the story ends, then "Fanout has courses on X." The strong plug is the answer to what
the body opened. In the approved framework the body is "what you actually need to learn" and the plug is where
those things are: "And you can find all of these only on Fanout."

Other plug styles, for alternates:

| Style | How it works |
|---|---|
| Answer plug | The body's open question is answered by Fanout |
| Tool-in-the-story | Fanout is the thing used inside the story |
| Contrast plug | Old way and Fanout way in one breath |
| One-moment plug | One concrete product moment, not a feature list |
| Insider plug | Framed as a recommendation to a friend |

Rules: say "Fanout" once; keep the story's voice when it appears; no feature list.

### Honesty

- Relatable first-person situations are fine.
- No personal results claims.
- Product claims only from `docs/product-facts.md`. Numbers about other companies must be public and accurate.

---

## 4. Self-critique (score 1 to 5 before saving)

| Dimension | 5 looks like |
|---|---|
| Hook | passes all five tests |
| Clarity | every line passes the stranger test |
| Storyline | each line follows from the one before |
| Specificity | a concrete thing in every beat, explained |
| Plug | Fanout once, as the answer, in the same voice |
| Voice | passes the read-aloud test; matches the tonality reference; no ad words |
| Truth | only product facts; no results claims |

---

## Credits

Adapted, condensed and rewritten for Fanout from these MIT-licensed projects (copyright notices kept as required):

- vyralcontent/content-skills (`viral-hooks`, `viral-captions-and-ctas`, `viral-short-form`), Copyright (c) 2026 Vyral, https://github.com/vyralcontent/content-skills
- motion-creative/motion-creative-plugin (`ugc-scripts`, `write-hooks`), Copyright (c) 2026 Motion, https://github.com/motion-creative/motion-creative-plugin
- gooseworks-ai/goose-skills (`make-video-ads` script craft and worked example), Copyright (c) 2026 GooseWorks, https://github.com/gooseworks-ai/goose-skills
- coreyhaines31/marketingskills (`ad-creative` hook system), Copyright (c) 2025 Corey Haines, https://github.com/coreyhaines31/marketingskills

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
documentation files, to deal in the Software without restriction, subject to the MIT License terms: the above
copyright notices and this permission notice shall be included in all copies or substantial portions.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND.
