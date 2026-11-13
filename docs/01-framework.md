# The approved framework

Approved on Nov 12, 2026. The final wording is the owner's own edit of the senior engineer script.
Use this for every new Fanout UGC script unless told otherwise.

## The six beats

| # | Beat | Exact wording to start from |
|---|---|---|
| 1 | Sauce hook | "I'm about to reveal some sauce for engineers that's not out there. This is all you need to know to actually become a **[role]**." |
| 2 | The research | "I searched YouTube. I read a bunch of blogs. I even asked a few **[role]s**." |
| 3 | The turn | "And I found out what you actually need to learn." |
| 4 | Five things | "One, … Two, … Three, … Four, … And five, …" Each is a name plus one plain clause or one example. |
| 5 | Fanout, once | "And you can find all of these only on Fanout." |
| 6 | Tagline | "Curated, mapped & complete." |

What each beat is doing:

1. **Sauce hook.** A secret is about to be shared, and the second sentence says who it is for and what it gets them.
2. **The research.** Normal words. It shows effort ("hustle") and is what every engineer has actually done.
3. **The turn.** She found the answer. The viewer now expects a list.
4. **Five things.** This is the value. The viewer learns what to learn before any product is mentioned.
5. **Fanout.** Named once, at the end, as where the five things live. No feature pitches.
6. **Tagline.** The brand line. Nothing after it.

Things the owner cut from earlier drafts, so do not add them back unasked: a "my manager said…" opening,
"it's five things", "the first lessons are free", "the link's right here".

## How to write the five things

- They are the content of the product: the five live archives for a whole-of-Fanout script, or the
  course's modules grouped into five for a single-course script. Take them from `docs/product-facts.md`.
- Every item must make sense to someone who has never heard the word. Explain it in the same sentence:
  - "…system design. **That's how** apps like Netflix and Uber handle millions of people."
  - "…inference engineering, **which is how** AI models actually run."
  - "…embeddings and vector search, **meaning** how an AI finds things by meaning instead of keywords."
  - "…the famous AI research papers, **for example:** 'Attention is all you need'."
- One clause each. Full sentences. No fragments, no "the landmark ones in order".
- Order them the way someone would learn them.

## Tonality layer

The framework fixes the beats. The owner sends a reference ad for the voice. Transcribe it
(`docs/04-research-methods.md`), list five phrases or sentence shapes that give it its voice, and re-voice the
beats with them. Transcripts are kept locally in `research/reference-ads/` (not in git). Two voices so far:

- **A fast list**: a promise, then a numbered list, each item one full sentence with a concrete detail and a payoff.
- **A friend sharing a find**: a personal feeling up front with "honestly"; sentences that run on with "because",
  "meaning", "which is"; small personal asides; closes with "It's crazy to me that…".

## The two scripts written on it

### Everything you need to become a senior engineer (owner's final)

> I'm about to reveal some sauce for engineers that's not out there. This is all you need to know to actually become a senior engineer.
>
> I searched YouTube. I read a bunch of blogs. I even asked a few senior engineers.
>
> And I found out what you actually need to learn.
>
> One, system design. That's how apps like Netflix and Uber handle millions of people.
>
> Two, the math behind Machine Learning, starting from the very basics.
>
> Three, the famous AI research papers, for example: "Attention is all you need".
>
> Four, inference engineering, which is how AI models actually run.
>
> And five, AI engineering, which is building real products with those models.
>
> And you can find all of these only on Fanout.
>
> Curated, mapped & complete.

### All you need to become an AI engineer (same beats, second tonality)

> I honestly wasn't going to share this, because this sauce for engineers is not out there. It's all you need to know to actually become an AI engineer.
>
> So I searched YouTube, read a bunch of blogs, and even asked a few AI engineers.
>
> And it comes down to five things.
>
> One is embeddings and vector search, meaning how an AI finds things by meaning instead of keywords.
>
> Two is RAG, which is how it looks up your own data before it answers.
>
> Three is what's actually happening inside the model, like attention and transformers.
>
> Four is optimization, meaning making a model faster and cheaper to run, which is the part that gives everyone a headache.
>
> And five is agents and MCP, which is how a model uses tools to get real work done.
>
> It's crazy to me that all five are in one place. And you can find them only on Fanout.
>
> Curated, mapped and complete.

Files: `scripts/final/`.

## Template for the next course

```
I'm about to reveal some sauce for engineers that's not out there. This is all you need to know to actually [become a ROLE / learn TOPIC].

I searched YouTube. I read a bunch of blogs. I even asked a few [ROLE]s.

And I found out what you actually need to learn.

One, [THING]. That's how [plain explanation].

Two, [THING], [starting from / which is / meaning …].

Three, [THING], for example: [one concrete example].

Four, [THING], which is [plain explanation].

And five, [THING], which is [plain explanation].

And you can find all of these only on Fanout.

Curated, mapped & complete.
```

## Length

The senior engineer final is 125 words: about 46 s spoken, 10 Veo clips. The AI engineer script is 157 words,
about 58 s. Aim for 120 to 160 words. Run `tools/check_script.py` on every script.

## Openings that were written and not used (keep for testing)

- "My manager said I wasn't ready for senior yet. I asked what I was missing, and I never got a real answer. So I researched everything myself."
- "I've been an engineer for five years, and I watched people who joined after me become senior. Nobody could tell me what they knew that I didn't."
- "It took me five years to figure out the sauce I'm about to give you." (a long struggle handed back short: the shape of the strongest organic outlier found)
- "AI engineering is honestly starting to scare me a little. Everyone says learn it, and nobody tells you what to actually learn." (closest to the second reference's opening)
