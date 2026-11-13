"""Free community sources: Reddit (Arctic Shift archive), Hacker News (Algolia), Stack Overflow (Stack Exchange API).

Reddit's own JSON API refuses scripts that are not logged in, so the free path reads the Arctic Shift
archive (https://github.com/ArthurHeitmann/arctic_shift). Its scores are captured some hours after a
post goes up, so they run lower than live Reddit; ScrapeCreators gives live scores.
"""
import datetime as dt
import html
import re
import time

from ..config import key
from ..net import FetchError, request_json
from ..store import make_item, ts_to_iso

ARCTIC = "https://arctic-shift.photon-reddit.com/api"
HN = "https://hn.algolia.com/api/v1"
SE = "https://api.stackexchange.com/2.3"


def strip_html(s):
    if not s:
        return None
    s = re.sub(r"<(br|p|/p|li)[^>]*>", "\n", s)
    s = re.sub(r"<[^>]+>", "", s)
    return re.sub(r"\n{3,}", "\n\n", html.unescape(s)).strip() or None


# ---------------------------------------------------------------- Reddit via Arctic Shift

def _arctic_posts(sub, after, before):
    d = request_json(f"{ARCTIC}/posts/search", params={
        "subreddit": sub, "after": after, "before": before, "limit": "auto",
        "fields": "id,title,selftext,score,num_comments,created_utc,subreddit"},
        timeout=90, retries=2)
    if d.get("error"):
        raise FetchError(d["error"])
    return d.get("data") or []


def reddit_sub(sub, days, log=print):
    end = dt.datetime.now(dt.timezone.utc)
    start = end - dt.timedelta(days=days)
    window = dt.timedelta(days=10)
    posts, cur, strikes = [], start, 0
    while cur < end:
        nxt = min(cur + window, end)
        try:
            rows = _arctic_posts(sub, cur.strftime("%Y-%m-%dT%H:%M"), nxt.strftime("%Y-%m-%dT%H:%M"))
            strikes = 0
        except FetchError as e:
            if "Timeout" not in str(e):  # a bad request will not get better with a smaller window
                log(f"  ! r/{sub}: {e}")
                break
            strikes += 1
            if strikes >= 6:  # the archive is overloaded; keep what we have and move on
                log(f"  ! r/{sub}: archive busy, stopped at {cur:%m-%d}")
                break
            time.sleep(10 * strikes)  # it asks us to slow down: back off before shrinking the window
            if strikes % 2 == 0 and window > dt.timedelta(days=2):
                window = window / 2
            continue
        posts += rows
        cur = nxt
        time.sleep(1.5)
    return [_reddit_item(p, sub) for p in posts
            if p.get("title") and not p["title"].lower().startswith(("[ removed", "[removed", "[deleted"))]


def _reddit_item(p, sub):
    text = p.get("selftext")
    if text in ("[removed]", "[deleted]"):
        text = None
    return make_item(
        "community", "reddit", str(p["id"]),
        url=f"https://www.reddit.com/r/{p.get('subreddit') or sub}/comments/{p['id']}/",
        author=f"r/{p.get('subreddit') or sub}", title=p.get("title"), text=text or None,
        published_at=ts_to_iso(p.get("created_utc")), query=f"subreddit:{sub}",
        metrics={"score": p.get("score"), "comments": p.get("num_comments")},
        extra={"provider": "arctic_shift"},
    )


def reddit_top_comments(post_id, k=6):
    try:
        d = request_json(f"{ARCTIC}/comments/tree", params={"link_id": f"t3_{post_id}", "limit": 300}, timeout=90, retries=2)
    except FetchError:
        return []
    top = [c.get("data") or {} for c in d.get("data") or [] if c.get("kind") != "more"]
    top = [c for c in top if c.get("body") and c.get("body") not in ("[removed]", "[deleted]")]
    top.sort(key=lambda c: -(c.get("score") or 0))
    return [{"score": c.get("score"), "text": c["body"][:600]} for c in top[:k]]


# ---------------------------------------------------------------- Hacker News

def hackernews(term, min_points=80, days=365):
    since = int(time.time()) - days * 86400
    d = request_json(f"{HN}/search", params={"query": term, "tags": "(story,ask_hn)",
                                             "numericFilters": f"points>{min_points},created_at_i>{since}",
                                             "hitsPerPage": 40})
    out = []
    for h in d.get("hits") or []:
        out.append(make_item(
            "community", "hackernews", str(h["objectID"]),
            url=f"https://news.ycombinator.com/item?id={h['objectID']}", author="Hacker News",
            title=h.get("title"), text=strip_html(h.get("story_text")), published_at=h.get("created_at"),
            query=f"search:{term}", metrics={"score": h.get("points"), "comments": h.get("num_comments")},
            extra={"link": h.get("url")},
        ))
    return out


def hn_top_comments(story_id, k=6):
    try:
        d = request_json(f"{HN}/items/{story_id}")
    except FetchError:
        return []
    kids = [c for c in d.get("children") or [] if c.get("text")]
    kids.sort(key=lambda c: -len(c.get("children") or []))  # most-replied first (HN hides comment points)
    return [{"score": len(c.get("children") or []), "text": strip_html(c["text"])[:600]} for c in kids[:k]]


# ---------------------------------------------------------------- Stack Overflow

def stackoverflow(tag, pages=1):
    out = []
    for page in range(1, pages + 1):
        d = request_json(f"{SE}/questions", params={
            "order": "desc", "sort": "votes", "tagged": tag, "site": "stackoverflow", "pagesize": 50,
            "page": page, "filter": "withbody", "key": key("STACKEXCHANGE_KEY")})
        for q in d.get("items") or []:
            out.append(make_item(
                "community", "stackoverflow", str(q["question_id"]),
                url=q.get("link"), author="Stack Overflow", title=html.unescape(q.get("title") or ""),
                text=(strip_html(q.get("body")) or "")[:2500] or None, published_at=ts_to_iso(q.get("creation_date")),
                query=f"tag:{tag}",
                metrics={"score": q.get("score"), "views": q.get("view_count"), "answers": q.get("answer_count")},
                extra={"tags": q.get("tags")},
            ))
        if not d.get("has_more"):
            break
        time.sleep(1)
    return out


def collect(cfg, log=print, reddit=True, out=None):
    c = cfg["community"]
    items = [] if out is None else out  # out may save each batch as it arrives
    if reddit:
        for sub in c.get("subreddits", []):
            got = reddit_sub(sub, c.get("reddit_days", 30), log=log)
            items += got
            log(f"  reddit r/{sub} (archive): {len(got)}")
    for term in c.get("search_terms", []):
        try:
            got = hackernews(term, c.get("hackernews_min_points", 80))
        except FetchError as e:
            log(f"  ! hn '{term}': {e}")
            continue
        items += got
        log(f"  hacker news '{term}': {len(got)}")
        time.sleep(0.5)
    for tag in c.get("stackoverflow_tags", []):
        try:
            got = stackoverflow(tag)
        except FetchError as e:
            log(f"  ! stackoverflow [{tag}]: {e}")
            continue
        items += got
        log(f"  stack overflow [{tag}]: {len(got)}")
        time.sleep(1)
    return items
