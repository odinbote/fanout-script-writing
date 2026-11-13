"""Command line for the Fanout script sourcing pipeline.

  bin/pipeline doctor                     which sources are switched on
  bin/pipeline run                        collect -> enrich -> rank -> pack (everything available)
  bin/pipeline collect --pillar ads,community
  bin/pipeline import-meta FILE...        ads saved from the Meta Ads connector
  bin/pipeline import-adlibrary FILE...   an advertiser's Ad Library page text (long-runners + copy)
  bin/pipeline import-amazon [DIR]        reviews / listing copy pasted into inputs/amazon
  bin/pipeline enrich                     transcripts + ad copy + top comments for the leaders
  bin/pipeline rank | pack | show --pillar ads
  bin/pipeline annotate ID --text-file F  attach ad copy read from the Ad Library page
  bin/pipeline check SCRIPT [--source A3] word count, Veo clip plan, overlap with the source item
"""
import argparse
import json
import pathlib
import sys
import time

from . import packs, rank, store
from .checks import clip_plan, competitor_hits, overlap
from .config import INPUTS, KEYS, key, load_config, load_env
from .sources import adlibrary_page, amazon, community_free, meta_connector, youtube_free
from .sources import scrapecreators as scm


def log(msg):
    print(msg, flush=True)


def sc_client():
    k = key("SCRAPECREATORS_API_KEY")
    return scm.Client(k, log=log) if k else None


def cmd_doctor(args, cfg, conn):
    log("Keys (.env):")
    for k, why in KEYS.items():
        log(f"  {'✓' if key(k) else '·'} {k:24} {why}")
    sc = bool(key("SCRAPECREATORS_API_KEY"))
    ap = bool(key("APIFY_TOKEN"))
    log("\nWhat runs:")
    log(f"  1 competitor ads   {'ScrapeCreators (copy + transcripts)' if sc else 'Meta Ads connector via the script-research skill (titles + run length)'}")
    log(f"  2 organic          YouTube (yt-dlp){' + TikTok + Instagram (ScrapeCreators)' if sc else ''}")
    log(f"  3 pain points      {'Reddit live, X, LinkedIn (ScrapeCreators) + ' if sc else 'Reddit archive (Arctic Shift) + '}Hacker News + Stack Overflow")
    log(f"  4 marketplace      {'Amazon via Apify' if ap else 'pasted Amazon text in inputs/amazon'}")
    counts = {p: len(store.fetch(conn, pillar=p)) for p in store.PILLARS}
    log("\nSwipe file: " + ", ".join(f"{p} {n}" for p, n in counts.items()))


class SavingList(list):
    """Collectors do `items += batch`; this writes each batch to the swipe file right away,
    so an interrupted run keeps everything collected so far."""

    def __init__(self, conn):
        super().__init__()
        self.conn, self.new = conn, 0

    def __iadd__(self, batch):
        batch = list(batch)
        self.new += store.upsert(self.conn, batch)
        self.extend(batch)
        return self

    def append(self, item):
        self.__iadd__([item])


def cmd_collect(args, cfg, conn):
    pillars = args.pillar.split(",") if args.pillar else list(store.PILLARS)
    sc = None if args.free_only else sc_client()
    out = SavingList(conn)
    if "ads" in pillars:
        if sc:
            log("Method 1 · competitor ads (ScrapeCreators)")
            scm.collect_ads(sc, cfg, log=log, out=out)
        else:
            log("Method 1 · competitor ads: no ScrapeCreators key; the script-research skill collects these "
                "through the Meta Ads connector and the Ad Library page (import-meta, import-adlibrary).")
    if "organic" in pillars:
        log("Method 2 · organic")
        youtube_free.collect(cfg, log=log, out=out)
        if sc:
            scm.collect_organic(sc, cfg, log=log, out=out)
    if "community" in pillars:
        log("Method 3 · pain points")
        if sc:
            scm.collect_community(sc, cfg, log=log, out=out)
        community_free.collect(cfg, log=log, reddit=not sc, out=out)
    if "marketplace" in pillars:
        log("Method 4 · marketplace")
        if key("APIFY_TOKEN") and not args.free_only:
            try:
                out += amazon.collect_apify(key("APIFY_TOKEN"), cfg, log=log)
            except Exception as e:  # noqa: BLE001
                log(f"  ! apify: {e}")
        out += amazon.import_dir(INPUTS / "amazon", log=log)
    if sc:
        log(f"ScrapeCreators credits used: {sc.credits_used}")
    log(f"New items: {out.new}")


def cmd_import_meta(args, cfg, conn):
    n = 0
    for f in args.files:
        items = meta_connector.load_file(f)
        n += store.upsert(conn, items)
        log(f"  {f}: {len(items)} ads")
    log(f"New ads: {n}")


def cmd_import_adlibrary(args, cfg, conn):
    n = 0
    for f in args.files:
        items = adlibrary_page.parse(pathlib.Path(f).read_text(errors="replace"), page_id=args.page_id)
        n += store.upsert(conn, items)
        with_copy = sum(1 for i in items if i.get("text"))
        log(f"  {f}: {len(items)} ads ({with_copy} with copy)")
    log(f"New ads: {n}")


def cmd_import_amazon(args, cfg, conn):
    log(f"New items: {store.upsert(conn, amazon.import_dir(args.dir or INPUTS / 'amazon', log=log))}")


def cmd_enrich(args, cfg, conn):
    rank.run(conn, cfg)
    top = args.top or cfg.get("scoring", {}).get("transcribe_top", 8)
    sc = sc_client()
    # works on exactly what the evidence packs will show
    # ads: copy + transcript for the longest runners
    for a in packs.select(conn, cfg, "ads")[:top]:
        if a.get("transcript") and a.get("text"):
            continue
        if sc:
            d = scm.ad_details(sc, a["id"].split(":", 1)[1])
            store.set_text(conn, a["id"], text=d.get("text") or a.get("text"), transcript=d.get("transcript"))
            log(f"  ad {a['id']}: copy {'✓' if d.get('text') else '·'} transcript {'✓' if d.get('transcript') else '·'}")
    # organic: transcripts for the top outliers
    for it in packs.select(conn, cfg, "organic"):
        if it.get("transcript") or it["extra"].get("transcript_tried"):
            continue
        text = None
        if it["source"] == "youtube":
            text = youtube_free.transcript(it["url"])
            time.sleep(8)  # YouTube answers 429 to rapid caption downloads
        if not text and sc and it["source"] in ("tiktok", "instagram", "youtube"):
            text = scm.transcript_for(sc, it)
        if text:
            store.set_text(conn, it["id"], transcript=text)
        log(f"  transcript {it['source']} {it.get('title') or it['id']}: {'✓' if text else '· (none or rate-limited)'}")
    # community: top comments for the leading posts
    for it in packs.select(conn, cfg, "community"):
        if it["extra"].get("top_comments") or it["source"] not in ("reddit", "hackernews"):
            continue
        if it["source"] == "hackernews":
            cs = community_free.hn_top_comments(it["id"].split(":", 1)[1])
        elif sc:
            cs = scm.reddit_comments(sc, it["url"])
        else:
            cs = community_free.reddit_top_comments(it["id"].split(":", 1)[1])
        it["extra"]["top_comments"] = cs
        store.set_metrics(conn, [it])
        log(f"  comments {it['source']} {(it.get('title') or '')[:60]}: {len(cs)}")


def cmd_rank(args, cfg, conn):
    log("Ranked: " + json.dumps(rank.run(conn, cfg)))


def cmd_pack(args, cfg, conn):
    rank.run(conn, cfg)
    outdir, mapping = packs.build(conn, cfg)
    log(f"Evidence packs: {outdir} ({len(mapping)} items)")


def cmd_run(args, cfg, conn):
    cmd_collect(args, cfg, conn)
    cmd_enrich(args, cfg, conn)
    cmd_pack(args, cfg, conn)


def cmd_show(args, cfg, conn):
    rank.run(conn, cfg)
    for it in store.fetch(conn, pillar=args.pillar, order_by_score=True)[: args.top]:
        label = (it.get("title") or it.get("text") or "").replace("\n", " ")[:70]
        log(f"{it['score']:>8} | {it['source']:13} | {(it.get('author') or '')[:22]:22} | {it.get('grade')} | {label}")


def cmd_annotate(args, cfg, conn):
    item_id = packs.latest_mapping().get(args.id, args.id)
    if not store.get(conn, item_id):
        sys.exit(f"no item {args.id}")
    text = pathlib.Path(args.text_file).read_text() if args.text_file else None
    tr = pathlib.Path(args.transcript_file).read_text() if args.transcript_file else None
    store.set_text(conn, item_id, text=text, transcript=tr)
    log(f"Updated {item_id}")


def cmd_check(args, cfg, conn):
    script = pathlib.Path(args.script).read_text()
    plan = clip_plan(script)
    log(f"{plan['words']} words · ~{plan['spoken_seconds']} s spoken · {len(plan['clips'])} Veo clips · "
        f"{plan['total_seconds']} s · ~${plan['est_cost_usd']}")
    for i, c in enumerate(plan["clips"], 1):
        log(f"  clip {i}: {c['seconds']} s, {c['words']} words{'  ← over 24 words, split it' if c['too_long'] else ''}")
    hits = competitor_hits(script, cfg["product"].get("competitor_names", []))
    log(f"  ⚠ COMPETITOR NAMED: {', '.join(hits)} (never allowed)" if hits else "  competitors: none named ✓")
    for code in args.source or []:
        item_id = packs.latest_mapping().get(code, code)
        it = store.get(conn, item_id)
        if not it:
            log(f"  ! no source item {code}")
            continue
        ov = overlap(script, f"{it.get('title') or ''}\n{it.get('text') or ''}\n{it.get('transcript') or ''}")
        log(f"  vs {code}: {ov['copied_share']:.0%} of words sit in shared runs of 5+ words")
        for r in ov["runs"][:5]:
            log(f"    “{r}”")


def main(argv=None):
    load_env()
    p = argparse.ArgumentParser(prog="pipeline", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--config")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("doctor")
    for name in ("collect", "run"):
        s = sub.add_parser(name)
        s.add_argument("--pillar", help="comma list: ads,organic,community,marketplace")
        s.add_argument("--free-only", action="store_true")
        s.add_argument("--top", type=int)
    s = sub.add_parser("import-meta"); s.add_argument("files", nargs="+")
    s = sub.add_parser("import-adlibrary"); s.add_argument("files", nargs="+"); s.add_argument("--page-id")
    s = sub.add_parser("import-amazon"); s.add_argument("dir", nargs="?")
    s = sub.add_parser("enrich"); s.add_argument("--top", type=int)
    sub.add_parser("rank")
    sub.add_parser("pack")
    s = sub.add_parser("show"); s.add_argument("--pillar"); s.add_argument("--top", type=int, default=20)
    s = sub.add_parser("annotate"); s.add_argument("id"); s.add_argument("--text-file"); s.add_argument("--transcript-file")
    s = sub.add_parser("check"); s.add_argument("script"); s.add_argument("--source", action="append")
    args = p.parse_args(argv)
    cfg = load_config(args.config)
    conn = store.connect()
    {"doctor": cmd_doctor, "collect": cmd_collect, "run": cmd_run, "import-meta": cmd_import_meta,
     "import-amazon": cmd_import_amazon, "import-adlibrary": cmd_import_adlibrary, "enrich": cmd_enrich, "rank": cmd_rank, "pack": cmd_pack,
     "show": cmd_show, "annotate": cmd_annotate, "check": cmd_check}[args.cmd](args, cfg, conn)


if __name__ == "__main__":
    main()
