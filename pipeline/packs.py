"""Evidence packs: the top items per method, written as Markdown for the script-writer skill,
plus evidence.json mapping short codes (A1, O1, C1, M1) to item ids."""
import datetime as dt
import json

from . import rank, store
from .config import OUTPUT

PREFIX = {"ads": "A", "organic": "O", "community": "C", "marketplace": "M"}
TITLES = {
    "ads": "Method 1 · Competitor ads that keep running",
    "organic": "Method 2 · Organic videos beating their account's average",
    "community": "Method 3 · Pain points people are upvoting",
    "marketplace": "Method 4 · What buyers say about rival products",
}


def _clip(s, n):
    s = (s or "").strip()
    return s if len(s) <= n else s[: n - 1].rsplit(" ", 1)[0] + "…"


def _block(code, it):
    m = it["metrics"]
    lines = [f"### [{code}] {it.get('author') or it['source']} · {it.get('grade') or ''}",
             f"- source: {it['source']} · {it.get('url') or ''}"]
    if it.get("published_at"):
        lines.append(f"- posted: {it['published_at'][:10]}")
    keep = {k: v for k, v in m.items() if v not in (None, [], "") and k not in ("start_ts", "end_ts", "pain_hits")}
    if keep:
        lines.append("- metrics: " + ", ".join(f"{k}={v}" for k, v in keep.items()))
    if it.get("query"):
        lines.append(f"- found by: {it['query']}")
    if it.get("title"):
        lines.append(f"- title: {_clip(it['title'], 300)}")
    if it.get("text"):
        lines.append("- text:\n\n" + "\n".join("  > " + ln for ln in _clip(it["text"], 1400).splitlines() if ln.strip()))
    if it.get("transcript"):
        lines.append("- transcript:\n\n  > " + _clip(it["transcript"], 1600))
    comments = it["extra"].get("top_comments") or []
    if comments:
        lines.append("- top comments:")
        lines += [f"  - ({c.get('score')}) {_clip(c.get('text'), 300)}" for c in comments[:5]]
    if it["pillar"] == "ads" and not it.get("text") and not it.get("transcript"):
        lines.append("- note: no ad copy yet (connector gives titles only). Read the Ad Library page or add a ScrapeCreators key.")
    return "\n".join(lines)


def select(conn, cfg, pillar):
    """The items an evidence pack shows for one method (also what enrich works on)."""
    n = cfg.get("scoring", {}).get("pack_size", 12)
    items = [i for i in store.fetch(conn, pillar=pillar, order_by_score=True) if i.get("score") is not None]
    if pillar == "marketplace":  # keep listings, then the best reviews of each kind
        listings = [i for i in items if i["source"] == "amazon_listing"]
        reviews = [i for i in items if i["source"] == "amazon"]
        low = [i for i in reviews if (i["metrics"].get("rating") or 0) <= 3][: n // 2]
        high = [i for i in reviews if (i["metrics"].get("rating") or 0) > 3][: n - len(low)]
        return listings + low + high
    if pillar == "organic":  # half short-form (closest to our UGC), half long-form
        shorts = [i for i in items if i["extra"].get("kind") == "short" or i["source"] in ("tiktok", "instagram")]
        longs = [i for i in items if i not in shorts]
        return shorts[: n // 2] + longs[: n - min(len(shorts), n // 2)]
    if pillar == "ads":  # one row per creative: variants are already counted in the grade
        seen, uniq = set(), []
        for it in items:
            key = (it["extra"].get("page_id") or it.get("author"),
                   rank._norm_text(it.get("text") or it.get("title")) or it["id"])
            if key not in seen:
                seen.add(key)
                uniq.append(it)
        return uniq[:n]
    if pillar == "community":  # no platform takes more than 60% of the pack
        cap, per, out = max(1, round(n * 0.6)), {}, []
        for it in items:
            title = (it.get("title") or "").lower()
            if title.startswith(("[ removed", "[removed", "[deleted")):
                continue
            if per.get(it["source"], 0) < cap:
                per[it["source"]] = per.get(it["source"], 0) + 1
                out.append(it)
            if len(out) == n:
                break
        return out
    return items[:n]


def build(conn, cfg, day=None):
    day = day or dt.date.today().isoformat()
    outdir = OUTPUT / day / "evidence"
    outdir.mkdir(parents=True, exist_ok=True)
    mapping, index = {}, [f"# Evidence packs · {day}", ""]
    for pillar in store.PILLARS:
        items = select(conn, cfg, pillar)
        if not items:
            index.append(f"- {TITLES[pillar]}: nothing collected yet")
            continue
        blocks = [f"# {TITLES[pillar]}", f"_{len(items)} items · ranked {day}_", ""]
        for k, it in enumerate(items, 1):
            code = f"{PREFIX[pillar]}{k}"
            mapping[code] = it["id"]
            blocks += [_block(code, it), ""]
        (outdir / f"{pillar}.md").write_text("\n".join(blocks))
        index.append(f"- [{TITLES[pillar]}]({pillar}.md): {len(items)} items, top: {items[0].get('grade')}")
    (outdir / "README.md").write_text("\n".join(index) + "\n")
    (outdir / "evidence.json").write_text(json.dumps(mapping, indent=1))
    return outdir, mapping


def latest_mapping():
    days = sorted(p for p in OUTPUT.glob("*/evidence/evidence.json"))
    return json.loads(days[-1].read_text()) if days else {}
