# Rules

Every rule here came from the owner's feedback. Check all of them before showing a script.

## Hard rules

1. **Never name a competitor** in a script. The list is `competitor_names` in `config/fanout.local.toml` and the
   checker flags every name on it. Companies used as examples of systems (Netflix, Uber) are fine.
2. **Product claims only from `docs/product-facts.md`.** No user counts, ratings or success rates unless the owner
   supplies them. No promises of jobs, promotions, salaries or passed interviews.
3. **No personal results.** First-person situations anyone could be in are fine ("I searched YouTube").
   Never "Fanout got me promoted" or anything else that reads as a testimonial.
4. **Across a batch, use the whole catalogue**: System Design, ML Math, AI Research, Inference Engineering,
   AI Engineering. Not system design only.
5. **Ask before any paid generation.** Script writing ends at the script. Video generation is a separate workflow.

## Writing rules

6. **Context for a cold viewer.** Every line must make sense to a normal person hearing it once, who has never
   heard of Fanout or the jargon. If a term needs explaining, explain it in the same sentence.
7. **Normal words, full sentences.** The way someone would tell a friend. No fragments, no compressed lines.
8. **One storyline.** I researched everything → I found out what to learn → here is the list → you can find it on
   Fanout. Each line follows from the one before.
9. **Value first, product last.** The list of what to learn is the body. Fanout is named once, at the end.
   No "Fanout shows you…" line per beat.
10. **The winning static is the message**: "Everything you need to become a senior engineer. In order." with the
    archive cards. The script should say that message out loud.
11. **Match the tonality reference closely.** The owner sends an ad for the voice. Transcribe it and use its
    sentence shapes. Do not invent a different voice.
12. **Study real scripts before writing.** Transcribe long-running ads in the niche and learn how they are built.
    Pain points come from ads, organic videos and communities together, never from one source alone.

## Lines that were rejected, and why

| Rejected line | What was wrong |
|---|---|
| "Juniors fix the bug. Seniors ask why the system let it happen." | Aphorisms. Generic advice with the product bolted on at the end. Ignored the static's message. |
| "System Design handles my design rounds. It builds Netflix and Uber piece by piece, so I never just sit there." | "I never just sit there" means nothing without the setup. No context. |
| "The landmark ones in order, each idea explained before I read it." | A fragment. A listener cannot tell what it refers to. |
| "Fanout shows you how Netflix and Uber are actually built, piece by piece." (one such line per beat) | Too salesy. |
| "Two, the math behind machine learning. Nobody tells you how much there is. I had to go back to the basics." | Good tone, says nothing. |
| "I used to give up by page two. Now I read a plain explanation of the idea first, then the paper." | Makes no sense to a listener. |
| "One. An account goes viral and your whole database slows down. Why? … It's called a hot partition." | A normal person will not follow a quiz of jargon. No context. |

The pattern in all of them: the line was written for someone who already knows the product and the field.

## Before showing a script

- Read each line as a stranger. Would you know what it means, on one listen?
- Is every term explained in its own sentence?
- Is Fanout named once, at the end?
- Does it follow the six beats in `docs/01-framework.md`?
- Did `tools/check_script.py` pass (no competitor names, no sentence over 24 words)?

## Talking to the owner

Replies are short: the script, two or three lines, the file link. One version, not a menu.
Details go in the script's sources file. Change only what was asked for.
