#!/usr/bin/env python3
"""Check a Fanout UGC script before it is shown or sent to video.

    python3 tools/check_script.py "scripts/final/<name>.txt"

Words, spoken seconds, the Veo clip plan and cost (the same packing as `bin/pipeline check`, from
pipeline/checks.py), plus the framework checks: no competitor names, no sentence over 24 words,
no ad words, Fanout named once, 120 to 160 words. Standard library only; runs on the system Python.

To compare a script with a source item in the swipe file, use `bin/pipeline check <script> --source A1`.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from pipeline.checks import clip_plan, competitor_hits, sentences  # noqa: E402

MAX_SENTENCE_WORDS = 24
TARGET_WORDS = (120, 160)
AD_WORDS = ["revolutionary", "game-changer", "game changer", "unlock", "level up", "supercharge",
            "cutting-edge", "seamless", "effortless"]


def competitor_names():
    """competitor_names from config/fanout.toml and config/fanout.local.toml (no TOML library needed)."""
    names = []
    for name in ("fanout.toml", "fanout.local.toml"):
        cfg = ROOT / "config" / name
        if cfg.exists():
            m = re.search(r"competitor_names\s*=\s*\[(.*?)\]", cfg.read_text(encoding="utf-8"), re.S)
            names += re.findall(r'"([^"]+)"', m.group(1)) if m else []
    return names


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    raw = Path(sys.argv[1]).read_text(encoding="utf-8")
    plan = clip_plan(raw)

    print(f"{plan['words']} words · ~{plan['spoken_seconds']} s spoken · {len(plan['clips'])} Veo clips · "
          f"{plan['total_seconds']} s · ~${plan['est_cost_usd']:.2f}")
    for i, c in enumerate(plan["clips"], 1):
        flag = "  ← over 24 words, split it" if c["too_long"] else ""
        print(f"  clip {i}: {c['seconds']} s, {c['words']} words  |  {c['text'][:70]}{flag}")

    problems = 0
    names = competitor_names()
    hits = competitor_hits(raw, names)
    if not names:
        print("  ! no competitor list found: copy config/fanout.local.example.toml to config/fanout.local.toml")
    elif hits:
        problems += 1
        print(f"  ✗ competitors named: {', '.join(hits)} (never allowed)")
    else:
        print("  ✓ no competitors named")

    for s in sentences(raw):
        n = len(s.split())
        if n > MAX_SENTENCE_WORDS:
            problems += 1
            print(f"  ✗ sentence over {MAX_SENTENCE_WORDS} words ({n}): {s[:80]}…")

    ads = [w for w in AD_WORDS if re.search(r"\b" + re.escape(w) + r"\b", raw, re.I)]
    if ads:
        problems += 1
        print(f"  ✗ ad words: {', '.join(ads)}")

    if not TARGET_WORDS[0] <= plan["words"] <= TARGET_WORDS[1]:
        print(f"  ! length is outside the usual {TARGET_WORDS[0]}-{TARGET_WORDS[1]} words")

    mentions = len(re.findall(r"\bFanout\b", raw))
    if mentions != 1:
        print(f"  ! Fanout is named {mentions} times (the framework names it once, at the end)")

    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
