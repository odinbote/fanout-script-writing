"""Import results from the Meta Ads connector's ads_library_search tool (run by Claude inside Claude Code).

The connector returns ad ids, page, link title and the delivery start time, which is enough to rank
ads by how long they have been running. It does not return body copy or video, so top ads get their
copy either from ScrapeCreators (enrich step) or by reading the public Ad Library page.

Accepted file shapes (JSON):
  {"query": "...", "status": "ACTIVE", "ads": [ ...connector ads... ]}
  [ {"query": ..., "status": ..., "ads": [...]}, ... ]
  or the raw tool result {"results": "<json string>"} / {"ads": [...]}
"""
import json
import time

from ..store import make_item, ts_to_iso


def _batches(blob):
    if isinstance(blob, list):
        for b in blob:
            yield from _batches(b)
        return
    if isinstance(blob, dict) and isinstance(blob.get("results"), str):
        inner = json.loads(blob["results"])
        inner.setdefault("query", blob.get("query"))
        inner.setdefault("status", blob.get("status"))
        yield from _batches(inner)
        return
    if isinstance(blob, dict) and "ads" in blob:
        yield blob


def norm_connector_ad(ad, query=None, status=None, now_ts=None):
    now_ts = now_ts or int(time.time())
    start = ad.get("ad_delivery_start_time") or ad.get("ad_creation_time")
    stop = ad.get("ad_delivery_stop_time")
    active = (status or "").upper() == "ACTIVE" or (stop in (None, "", 0))
    start = int(start) if start else None
    stop = int(stop) if stop else None
    days = max(0, ((now_ts if active else (stop or start)) - start) // 86400) if start else None
    bodies = ad.get("ad_creative_bodies") or []
    titles = ad.get("ad_creative_link_titles") or ([ad["ad_creative_link_title"]] if ad.get("ad_creative_link_title") else [])
    return make_item(
        "ads", "meta_ads", str(ad["id"]),
        url=ad.get("ad_snapshot_url") or f"https://www.facebook.com/ads/library/?id={ad['id']}",
        author=ad.get("page_name"),
        title=" | ".join(titles) or None,
        text="\n\n".join(bodies) or None,
        published_at=ts_to_iso(start),
        query=query,
        metrics={"days_active": days, "is_active": active, "start_ts": start, "end_ts": stop},
        extra={"provider": "meta_connector", "page_id": str(ad.get("page_id") or ""), "currency": ad.get("currency")},
    )


COMPACT = ("id", "page_id", "page_name", "ad_delivery_start_time", "ad_creative_link_title")


def load_file(path):
    """Ads may be full connector objects or compact rows: [id, page_id, page_name, start_ts, link_title]."""
    with open(path) as f:
        blob = json.load(f)
    items = []
    for b in _batches(blob):
        for ad in b.get("ads") or []:
            if isinstance(ad, list):
                ad = dict(zip(COMPACT, ad))
            items.append(norm_connector_ad(ad, query=b.get("query"), status=b.get("status")))
    return items
