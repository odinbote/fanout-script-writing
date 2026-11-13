"""Scoring per method. Each item gets a numeric score (higher = stronger evidence) and a readable grade.

ads          days the ad has been running (spend you can see) + how many variants of it are live
organic      views versus the account's own median (outliers), or versus followers when that is all we have
community    engagement percentile within its platform, boosted when the post reads like a pain point
marketplace  helpful votes on the review; the grade says what the review is good for
"""
import math
import re
import statistics
from collections import defaultdict

from . import store

AD_GRADES = [(60, "Long-Runner"), (30, "Performer"), (14, "Solid"), (7, "Testing"), (0, "New")]


def _norm_text(s):
    return re.sub(r"[^a-z0-9 ]", "", (s or "").lower())[:160]


def score_ads(items):
    groups = defaultdict(list)
    for it in items:
        key = (it["extra"].get("page_id") or it.get("author"), _norm_text(it.get("text") or it.get("title")))
        groups[key].append(it)
    out = []
    for it in items:
        days = it["metrics"].get("days_active") or 0
        key = (it["extra"].get("page_id") or it.get("author"), _norm_text(it.get("text") or it.get("title")))
        # each Ad Library entry may say "N ads use this creative and text"; sum those across the copy group
        group = groups[key] if key[1] else [it]
        variants = sum(max(1, g["metrics"].get("variants_listed") or 1) for g in group)
        it["metrics"]["variants"] = variants
        grade = next(g for t, g in AD_GRADES if days >= t)
        if not it["metrics"].get("is_active", True) and days >= 30:
            grade += " (stopped)"
        score = days + 6 * math.log2(variants) + (5 if it["metrics"].get("is_active") else 0)
        out.append((it["id"], round(score, 2), f"{grade}, {days}d" + (f", {variants} variants" if variants > 1 else "")))
    return out


def score_organic(items):
    def group(it):  # shorts and long videos have different baselines
        return (it["source"], it.get("author"), it["extra"].get("kind") or "")

    by_author = defaultdict(list)
    for it in items:
        v = it["metrics"].get("views")
        if v:
            by_author[group(it)].append(v)
    medians = {k: statistics.median(v) for k, v in by_author.items() if len(v) >= 5}
    out = []
    for it in items:
        v = it["metrics"].get("views") or 0
        med = medians.get(group(it))
        followers = it["metrics"].get("followers")
        if med:
            ratio, basis = v / med if med else 0, "x channel median"
        elif followers:
            ratio, basis = v / max(followers, 1), "x followers"
        else:
            ratio, basis = None, None
        it["metrics"]["outlier"] = round(ratio, 2) if ratio is not None else None
        if ratio is None:
            score = math.log10(v + 1)  # no baseline: raw reach only, ranks below real outliers
            grade = f"{v:,} views (no baseline)"
        else:
            score = ratio * 10 + math.log10(v + 1)
            label = "Mega outlier" if ratio >= 10 else "Outlier" if ratio >= 3 else "Above average" if ratio >= 1.5 else "Normal"
            grade = f"{label}: {ratio:.1f}{basis}, {v:,} views"
        out.append((it["id"], round(score, 2), grade))
    return out


def _engagement(it):
    m = it["metrics"]
    s = it["source"]
    if s == "reddit":
        return (m.get("score") or 0) + 2 * (m.get("comments") or 0)
    if s == "hackernews":
        return (m.get("score") or 0) + 1.5 * (m.get("comments") or 0)
    if s == "stackoverflow":
        return 10 * (m.get("score") or 0) + (m.get("views") or 0) / 500
    if s == "x":
        return (m.get("likes") or 0) + 3 * (m.get("reposts") or 0) + 2 * (m.get("replies") or 0) + 2 * (m.get("bookmarks") or 0)
    if s == "linkedin":
        return (m.get("likes") or 0) + 3 * (m.get("comments") or 0)
    return 0


def _word_re(words):
    return [(w, re.compile(r"(?<![a-z])" + re.escape(w.lower()))) for w in words]


def score_community(items, pain_words, topic_words=(), learning_words=()):
    """Engagement percentile within the platform, x pain boost, x topic relevance.
    Pain and topic words are matched in the title and the first 500 characters only, so long
    bodies do not collect accidental hits."""
    pain, topic, learn = _word_re(pain_words), _word_re(topic_words), _word_re(learning_words)
    by_src = defaultdict(list)
    for it in items:
        by_src[it["source"]].append(_engagement(it))
    for k in by_src:
        by_src[k].sort()
    out = []
    for it in items:
        e = _engagement(it)
        vals = by_src[it["source"]]
        pct = sum(1 for x in vals if x <= e) / len(vals)
        title = (it.get("title") or "").lower()
        head = f"{title} {(it.get('text') or '')[:500].lower()}"
        hits = sorted({w for w, rx in pain if rx.search(head)})
        tags = " ".join(it["extra"].get("tags") or []).replace("-", " ")
        if not topic or any(rx.search(title) for _, rx in topic):
            rel = 2.0
        elif any(rx.search(f"{head} {tags}") for _, rx in topic):
            rel = 1.5
        elif any(rx.search(head) for _, rx in learn):
            rel = 1.0
        else:
            rel = 0.4
        on_topic = rel >= 1.0
        boost = (1 + min(len(hits), 3) * 0.15) * rel
        if it["source"] == "hackernews":  # launches are not pain; Ask HN threads usually are
            boost *= 0.5 if title.startswith("show hn") else 1.3 if title.startswith("ask hn") else 1.0
        it["metrics"]["pain_hits"] = hits
        score = round(100 * pct * boost, 2)
        label = "Viral" if pct >= 0.95 else "Strong" if pct >= 0.8 else "Normal"
        grade = (f"{label} (top {max(1, round(100 * (1 - pct)))}% of {it['source']})"
                 + (f", pain: {', '.join(hits[:4])}" if hits else "") + ("" if on_topic else ", off-topic"))
        out.append((it["id"], score, grade))
    return out


def score_marketplace(items):
    out = []
    for it in items:
        if it["source"] == "amazon_listing":
            out.append((it["id"], 1000.0, "Listing copy"))
            continue
        r = it["metrics"].get("rating") or 0
        h = it["metrics"].get("helpful") or 0
        use = "objection / rival weakness" if r <= 2 else "nuanced (likes + gaps)" if r < 4 else "desire language"
        score = 2 * h + min(len(it.get("text") or "") / 300, 5) + (3 if 2 < r < 4 else 0)
        out.append((it["id"], round(score, 2), f"{r:g}★ {use}, {h} helpful"))
    return out


def run(conn, cfg):
    totals = {}
    for pillar in store.PILLARS:
        items = store.fetch(conn, pillar=pillar)
        if not items:
            continue
        if pillar == "ads":
            rows = score_ads(items)
        elif pillar == "organic":
            rows = score_organic(items)
        elif pillar == "community":
            c = cfg["community"]
            rows = score_community(items, c.get("pain_words", []), c.get("topic_words", []), c.get("learning_words", []))
        else:
            rows = score_marketplace(items)
        store.set_scores(conn, rows)
        store.set_metrics(conn, items)  # persist derived metrics (variants, outlier, pain hits)
        totals[pillar] = len(rows)
    return totals
