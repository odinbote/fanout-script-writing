"""Script checks: how close a script sits to its source, and how it packs into Veo clips."""
import re

VEO_WORDS_PER_S = 2.7      # measured on the Fanout UGC clips (Oct 29)
VEO_COST_PER_S = 0.40      # google/veo-3.1 full model with audio


def _words(s):
    return re.findall(r"[a-z0-9']+", (s or "").lower())


def overlap(script, source, min_run=5):
    """Shared word runs of at least min_run words, longest first, plus the share of script words inside them."""
    a, b = _words(script), _words(source)
    if not a or not b:
        return {"runs": [], "copied_share": 0.0}
    grams = {}
    for i in range(len(b) - min_run + 1):
        grams.setdefault(tuple(b[i:i + min_run]), i)
    covered, runs, i = set(), [], 0
    while i <= len(a) - min_run:
        key = tuple(a[i:i + min_run])
        if key in grams:
            j, length = grams[key], min_run
            while i + length < len(a) and j + length < len(b) and a[i + length] == b[j + length]:
                length += 1
            runs.append(" ".join(a[i:i + length]))
            covered.update(range(i, i + length))
            i += length
        else:
            i += 1
    runs.sort(key=lambda r: -len(r.split()))
    return {"runs": runs, "copied_share": round(len(covered) / len(a), 3)}


def competitor_hits(text, names):
    """Competitor names that appear in the script (case-insensitive, whole words)."""
    low = (text or "").lower()
    return [n for n in names if re.search(r"(?<![a-z])" + re.escape(n.lower()) + r"(?![a-z])", low)]


def sentences(text):
    parts = re.split(r"(?<=[.!?…])\s+|\n+", text.strip())
    return [p.strip() for p in parts if p.strip()]


PACK_TARGET, PACK_MAX_8S, BUCKETS = 17, 26, [(11, 4), (17, 6), (24, 8)]


def clip_plan(text):
    """Mirror pack_clips() in the UGC video pipeline (ugc_pipeline.py): whole sentences packed in order up to
    17 words per clip; buckets <=11 words 4 s, <=17 6 s, <=24 8 s; a sentence over 26 words is
    split first (here at its commas, an approximation of split_script)."""
    t = re.sub(r"\s+", " ", text.replace("…", "...")).strip()
    t = re.sub(r"\s*\.\.\.\s*", ", ", t)
    t = re.sub(r"\b([A-Za-z]+)\.sh\b", r"\1 dot ess aitch", t)
    units = []
    for s in [x.strip() for x in re.split(r"(?<=[.!?])\s+", t) if x.strip()]:
        if len(s.split()) > PACK_MAX_8S and "," in s:
            units += [p.strip() + "," for p in s.split(",") if p.strip()]
        else:
            units.append(s)
    packed, cur = [], ""
    for u in units:
        cand = (cur + " " + u).strip()
        if cur and len(cand.split()) > PACK_TARGET:
            packed.append(cur)
            cur = u
        else:
            cur = cand
    if cur:
        packed.append(cur)
    plan = []
    for line in packed:
        n = len(line.split())
        secs = next((d for mx, d in BUCKETS if n <= mx), 8)
        plan.append({"words": n, "seconds": secs, "text": line, "too_long": n > 24})
    total_s = sum(p["seconds"] for p in plan)
    return {"clips": plan, "total_seconds": total_s, "est_cost_usd": round(total_s * VEO_COST_PER_S, 2),
            "words": len(text.split()), "spoken_seconds": round(len(text.split()) / VEO_WORDS_PER_S, 1)}
