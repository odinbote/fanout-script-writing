"""ScrapeCreators: one key for Meta Ad Library (copy + transcripts), TikTok, Instagram, YouTube,
Reddit, X and LinkedIn. Docs: https://docs.scrapecreators.com/llms-full.txt

Normalizers are pure functions (tested against the docs' sample responses in tests/fixtures/sc).
"""
import re
import time

from ..net import FetchError, request_json
from ..store import make_item, ts_to_iso

BASE = "https://api.scrapecreators.com"


class Client:
    def __init__(self, api_key, pause=0.4, log=print):
        self.key = api_key
        self.pause = pause
        self.log = log
        self.credits_used = 0

    def get(self, path, **params):
        data = request_json(BASE + path, params=params, headers={"x-api-key": self.key}, timeout=120)
        self.credits_used += int(data.get("credits_charged") or 1) if isinstance(data, dict) else 1
        time.sleep(self.pause)
        return data

    def safe(self, path, **params):
        try:
            return self.get(path, **params)
        except FetchError as e:
            self.log(f"  ! {path}: {e}")
            return None


def _int(v):
    if v in (None, "", "None"):
        return None
    try:
        return int(float(str(v).replace(",", "")))
    except ValueError:
        return None


def vtt_to_text(vtt):
    if not vtt:
        return None
    if "-->" not in vtt:
        return vtt.strip() or None
    out = []
    for line in vtt.splitlines():
        line = line.strip()
        if not line or line == "WEBVTT" or "-->" in line or line.isdigit() or line.startswith(("Kind:", "Language:", "NOTE")):
            continue
        line = re.sub(r"<[^>]+>", "", line)
        if not out or out[-1] != line:
            out.append(line)
    return " ".join(out) or None


# ---------------------------------------------------------------- Meta Ad Library

def _ad_body(snap):
    body = snap.get("body")
    if isinstance(body, dict):
        body = body.get("text")
    texts = [body] if body else []
    for card in snap.get("cards") or []:
        if isinstance(card, dict) and card.get("body") and card.get("body") not in texts:
            texts.append(card["body"])
    return "\n\n".join(t for t in texts if t) or None


def norm_fb_ad(r, query=None, now_ts=None):
    snap = r.get("snapshot") or {}
    start = _int(r.get("start_date"))
    end = _int(r.get("end_date"))
    active = bool(r.get("is_active"))
    now_ts = now_ts or int(time.time())
    days = None
    if start:
        days = max(0, ((now_ts if active else (end or start)) - start) // 86400)
    videos = snap.get("videos") or []
    ad_id = str(r.get("ad_archive_id"))
    return make_item(
        "ads", "meta_ads", ad_id,
        url=f"https://www.facebook.com/ads/library/?id={ad_id}",
        author=r.get("page_name") or snap.get("page_name"),
        title=snap.get("title"),
        text=_ad_body(snap),
        published_at=ts_to_iso(start),
        query=query,
        metrics={"days_active": days, "is_active": active, "start_ts": start, "end_ts": end,
                 "page_likes": _int(snap.get("page_like_count"))},
        extra={"provider": "scrapecreators", "page_id": str(r.get("page_id") or snap.get("page_id") or ""),
               "format": snap.get("display_format"), "cta": snap.get("cta_text"), "link_url": snap.get("link_url"),
               "video_url": (videos[0].get("video_hd_url") or videos[0].get("video_sd_url")) if videos else None,
               "platforms": r.get("publisher_platform")},
    )


def norm_fb_ad_detail(d):
    """Body + transcript from /v1/facebook/adLibrary/ad (with get_transcript=true)."""
    snap = d.get("snapshot") or {}
    transcript = d.get("transcript")
    if isinstance(transcript, dict):
        transcript = transcript.get("transcript")
    return {"text": _ad_body(snap), "transcript": vtt_to_text(transcript) if isinstance(transcript, str) else None}


def collect_ads(sc, cfg, log=print, out=None):
    a = cfg["ads"]
    items = [] if out is None else out  # out may save each batch as it arrives
    for comp in a.get("competitors", []):
        got, cursor = 0, None
        while got < a.get("max_ads_per_competitor", 60):
            params = {"pageId": comp.get("page_id"), "companyName": None if comp.get("page_id") else comp["name"],
                      "status": "ALL", "sort_by": "total_impressions", "cursor": cursor, "trim": "false"}
            data = sc.safe("/v1/facebook/adLibrary/company/ads", **params)
            if not data or not data.get("results"):
                break
            batch = [norm_fb_ad(r, query=f"competitor:{comp['name']}") for r in data["results"]]
            items += batch
            got += len(batch)
            cursor = data.get("cursor")
            if not cursor:
                break
        log(f"  meta ads  {comp['name']}: {got}")
    for term in a.get("search_terms", []):
        for country in a.get("countries", ["US"])[:2]:
            data = sc.safe("/v1/facebook/adLibrary/search/ads", query=term, country=country, status="ALL",
                           sort_by="total_impressions", search_type="keyword_unordered", trim="false")
            rows = (data or {}).get("searchResults") or []
            items += [norm_fb_ad(r, query=f"search:{term}") for r in rows]
            log(f"  meta ads  '{term}' {country}: {len(rows)}")
    return items


def ad_details(sc, ad_id):
    d = sc.safe("/v1/facebook/adLibrary/ad", id=ad_id, get_transcript="true")
    return norm_fb_ad_detail(d) if d else {}


# ---------------------------------------------------------------- organic

def norm_tiktok(a, query=None):
    st = a.get("statistics") or {}
    au = a.get("author") or {}
    handle = au.get("unique_id")
    vid = str(a.get("aweme_id"))
    return make_item(
        "organic", "tiktok", vid,
        url=a.get("url") or (f"https://www.tiktok.com/@{handle}/video/{vid}" if handle else None),
        author=handle, text=a.get("desc"), published_at=ts_to_iso(a.get("create_time")), query=query,
        metrics={"views": _int(st.get("play_count")), "likes": _int(st.get("digg_count")),
                 "comments": _int(st.get("comment_count")), "shares": _int(st.get("share_count")),
                 "saves": _int(st.get("collect_count")), "followers": _int(au.get("follower_count"))},
    )


def norm_ig_reel_search(r, query=None):
    own = r.get("owner") or {}
    return make_item(
        "organic", "instagram", str(r.get("shortcode") or r.get("id")),
        url=r.get("url"), author=own.get("username"), text=r.get("caption"),
        published_at=r.get("taken_at"), query=query,
        metrics={"views": _int(r.get("video_view_count") or r.get("play_count")), "likes": _int(r.get("like_count")),
                 "comments": _int(r.get("comment_count")), "followers": _int(own.get("follower_count"))},
    )


def norm_ig_user_reel(it, query=None):
    cap = it.get("caption")
    cap = cap.get("text") if isinstance(cap, dict) else cap
    user = it.get("user") or it.get("owner") or {}
    return make_item(
        "organic", "instagram", str(it.get("code") or it.get("id")),
        url=it.get("url") or (f"https://www.instagram.com/reel/{it['code']}/" if it.get("code") else None),
        author=user.get("username"), text=cap, published_at=it.get("created_at") or ts_to_iso(it.get("taken_at")),
        query=query,
        metrics={"views": _int(it.get("play_count") or it.get("ig_play_count")), "likes": _int(it.get("like_count")),
                 "comments": _int(it.get("comment_count"))},
    )


def norm_yt(s, query=None, channel=None):
    ch = s.get("channel")
    if isinstance(ch, dict):
        ch = ch.get("handle") or ch.get("title") or ch.get("name")
    return make_item(
        "organic", "youtube", str(s.get("id")),
        url=s.get("url") or f"https://www.youtube.com/watch?v={s.get('id')}",
        author=channel or ch, title=s.get("title"), text=s.get("description"),
        published_at=s.get("publishDate") or s.get("publishedTime"), query=query,
        metrics={"views": _int(s.get("viewCountInt")), "likes": _int(s.get("likeCountInt")),
                 "comments": _int(s.get("commentCountInt")),
                 "duration_s": (_int(s.get("durationMs")) or 0) // 1000 or _int(s.get("lengthSeconds"))},
        extra={"kind": s.get("type")},
    )


def collect_organic(sc, cfg, log=print, out=None):
    o = cfg["organic"]
    items = [] if out is None else out  # out may save each batch as it arrives
    for term in o.get("search_terms", []):
        d = sc.safe("/v1/tiktok/search/keyword", query=term, sort_by="most-liked", date_posted="last-6-months")
        rows = (d or {}).get("search_item_list") or []
        items += [norm_tiktok(a, query=f"search:{term}") for a in rows]
        d = sc.safe("/v2/instagram/reels/search", query=term, date_posted="last-year")
        reels = (d or {}).get("reels") or []
        items += [norm_ig_reel_search(r, query=f"search:{term}") for r in reels]
        d = sc.safe("/v1/youtube/search", query=term, type="shorts", sortBy="popular", uploadDate="this_year")
        shorts = ((d or {}).get("shorts") or []) + ((d or {}).get("videos") or [])
        items += [norm_yt(s, query=f"search:{term}") for s in shorts]
        log(f"  organic '{term}': tiktok {len(rows)}, instagram {len(reels)}, youtube {len(shorts)}")
    for h in o.get("tiktok_accounts", []):
        d = sc.safe("/v3/tiktok/profile/videos", handle=h, sort_by="latest", trim="true")
        rows = (d or {}).get("aweme_list") or []
        items += [norm_tiktok(a, query=f"account:{h}") for a in rows]
        log(f"  tiktok @{h}: {len(rows)}")
    for h in o.get("instagram_accounts", []):
        d = sc.safe("/v1/instagram/user/reels", handle=h, trim="true")
        rows = (d or {}).get("items") or []
        items += [norm_ig_user_reel(it, query=f"account:{h}") for it in rows]
        log(f"  instagram @{h}: {len(rows)}")
    return items


def transcript_for(sc, item):
    src, url = item["source"], item.get("url")
    if src == "tiktok":
        d = sc.safe("/v1/tiktok/video/transcript", url=url, use_ai_as_fallback="true")
        return vtt_to_text((d or {}).get("transcript"))
    if src == "instagram":
        d = sc.safe("/v2/instagram/media/transcript", url=url)
        ts = (d or {}).get("transcripts") or []
        return " ".join(t.get("text", "") for t in ts if t.get("text")) or None
    if src == "youtube":
        d = sc.safe("/v1/youtube/video/transcript", url=url)
        return (d or {}).get("transcript_only_text")
    if src == "linkedin":
        d = sc.safe("/v1/linkedin/post/transcript", url=url)
        return (d or {}).get("transcript")
    if src == "meta_ads":
        return ad_details(sc, item["id"].split(":", 1)[1]).get("transcript")
    return None


# ---------------------------------------------------------------- community

def norm_reddit(p, query=None):
    pid = str(p.get("id"))
    url = p.get("url") or ""
    if "/comments/" not in url:
        url = f"https://www.reddit.com/r/{p.get('subreddit')}/comments/{pid}/"
    return make_item(
        "community", "reddit", pid,
        url=url, author=f"r/{p.get('subreddit')}", title=p.get("title"), text=p.get("selftext") or None,
        published_at=ts_to_iso(p.get("created_utc")), query=query,
        metrics={"score": _int(p.get("score") or p.get("ups")), "comments": _int(p.get("num_comments")),
                 "upvote_ratio": p.get("upvote_ratio")},
    )


def norm_reddit_comments(d, k=6):
    cs = [c for c in (d or {}).get("comments") or [] if isinstance(c, dict) and c.get("body")]
    cs.sort(key=lambda c: -(_int(c.get("score")) or 0))
    return [{"score": _int(c.get("score")), "text": c["body"][:600]} for c in cs[:k]]


def norm_linkedin(p, query=None):
    au = p.get("author") or {}
    url = p.get("url")
    return make_item(
        "community", "linkedin", re.sub(r"\W+", "_", url or "")[-80:],
        url=url, author=au.get("name"), text=p.get("description"), published_at=p.get("datePublished"), query=query,
        metrics={"likes": _int(p.get("likeCount")), "comments": _int(p.get("commentCount")),
                 "followers": _int(au.get("followers"))},
        extra={"top_comments": [{"text": (c.get("text") or "")[:400], "score": _int(c.get("reactionCount"))}
                                for c in (p.get("comments") or [])[:5]]},
    )


def norm_tweet(p, query=None):
    lg = p.get("legacy") or {}
    views = (p.get("views") or {}).get("count")
    url = p.get("url") or ""
    m = re.search(r"x\.com/([^/]+)/status", url)
    return make_item(
        "community", "x", str(p.get("rest_id")),
        url=url, author=m.group(1) if m else None, text=lg.get("full_text"), published_at=lg.get("created_at"),
        query=query,
        metrics={"likes": _int(lg.get("favorite_count")), "reposts": _int(lg.get("retweet_count")),
                 "replies": _int(lg.get("reply_count")), "quotes": _int(lg.get("quote_count")),
                 "bookmarks": _int(lg.get("bookmark_count")), "views": _int(views)},
    )


def collect_community(sc, cfg, log=print, out=None):
    c = cfg["community"]
    items = [] if out is None else out  # out may save each batch as it arrives
    for sub in c.get("subreddits", []):
        d = sc.safe("/v1/reddit/subreddit", subreddit=sub, sort="top", timeframe="month", trim="false")
        rows = (d or {}).get("posts") or []
        items += [norm_reddit(p, query=f"subreddit:{sub}") for p in rows]
        log(f"  reddit r/{sub}: {len(rows)}")
    for term in c.get("search_terms", []):
        d = sc.safe("/v1/reddit/search", query=term, sort="top", timeframe="year")
        rows = (d or {}).get("posts") or []
        items += [norm_reddit(p, query=f"search:{term}") for p in rows]
        d = sc.safe("/v1/twitter/search/posts", query=term)
        tw = (d or {}).get("posts") or []
        items += [norm_tweet(p, query=f"search:{term}") for p in tw]
        d = sc.safe("/v1/linkedin/search/posts", query=term, date_posted="last-year")
        li = (d or {}).get("posts") or []
        items += [norm_linkedin(p, query=f"search:{term}") for p in li]
        log(f"  '{term}': reddit {len(rows)}, x {len(tw)}, linkedin {len(li)}")
    return items


def reddit_comments(sc, url):
    return norm_reddit_comments(sc.safe("/v1/reddit/post/comments", url=url, trim="true"))
