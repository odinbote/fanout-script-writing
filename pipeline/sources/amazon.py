"""Amazon reviews and listing copy.

With APIFY_TOKEN: runs the junglee/amazon-reviews-scraper actor (reviews + product details).
Without it: parses text pasted from Amazon into inputs/amazon/<product>/reviews.txt and listing.txt.
Note: Amazon's terms forbid automated scraping of its pages; the Apify route is the user's call.
"""
import pathlib
import re

from ..net import request_json
from ..store import make_item

ACTOR = "junglee~amazon-reviews-scraper"


def helpful_votes(s):
    if not s:
        return 0
    if isinstance(s, (int, float)):
        return int(s)
    m = re.search(r"([\d,]+|One|one) (?:people|person) found this helpful", s)
    if not m:
        return 0
    return 1 if m.group(1).lower() == "one" else int(m.group(1).replace(",", ""))


def _review_item(product, asin, rid, rating, title, body, helpful, date=None, url=None, verified=None, query=None):
    return make_item(
        "marketplace", "amazon", f"{asin or product}:{rid}",
        url=url, author=product, title=title, text=body, published_at=date, query=query or f"product:{product}",
        metrics={"rating": rating, "helpful": helpful},
        extra={"kind": "review", "asin": asin, "verified": verified},
    )


def _listing_item(product, asin, title, text, url=None, rating=None, reviews=None):
    return make_item(
        "marketplace", "amazon_listing", asin or re.sub(r"\W+", "_", product),
        url=url, author=product, title=title, text=text, query=f"product:{product}",
        metrics={"rating": rating, "reviews": reviews}, extra={"kind": "listing", "asin": asin},
    )


def collect_apify(token, cfg, log=print):
    m = cfg["marketplace"]
    body = {"productUrls": [{"url": p["url"]} for p in m.get("products", [])],
            "maxReviews": m.get("max_reviews", 100), "sort": "helpful", "filterByRatings": ["allStars"],
            "includeGdprSensitive": False, "scrapeProductDetails": True, "deduplicateRedirectedAsins": True}
    rows = request_json(f"https://api.apify.com/v2/acts/{ACTOR}/run-sync-get-dataset-items",
                        params={"timeout": 600}, headers={"Authorization": f"Bearer {token}"}, body=body,
                        timeout=660, retries=1)
    names = {re.search(r"/dp/([A-Z0-9]{10})", p["url"]).group(1): p["name"] for p in m.get("products", [])
             if re.search(r"/dp/([A-Z0-9]{10})", p["url"])}
    items, listings = [], {}
    for r in rows if isinstance(rows, list) else []:
        if r.get("error"):
            log(f"  ! amazon {r.get('input') or r.get('url')}: {r.get('errorDescription') or r['error']}")
            continue
        asin = r.get("productAsin")
        name = names.get(asin, asin)
        if r.get("reviewDescription"):
            rid = (re.search(r"customer-reviews/([A-Z0-9]+)", r.get("reviewUrl") or "") or [None, r.get("position")])[1]
            items.append(_review_item(name, asin, rid, r.get("ratingScore"), r.get("reviewTitle"),
                                      r["reviewDescription"], helpful_votes(r.get("reviewReaction")),
                                      date=r.get("reviewedIn"), url=r.get("reviewUrl"), verified=r.get("isVerified")))
        prod = r.get("product")
        if isinstance(prod, dict) and asin not in listings:
            parts = [prod.get("description"), "\n".join(prod.get("features") or []), prod.get("bookDescription")]
            listings[asin] = _listing_item(name, asin, prod.get("title"), "\n\n".join(p for p in parts if p) or None,
                                           url=prod.get("url"), rating=prod.get("stars"), reviews=prod.get("reviewsCount"))
    log(f"  amazon (apify): {len(items)} reviews, {len(listings)} listings")
    return items + list(listings.values())


# ---------------------------------------------------------------- pasted text

STAR = re.compile(r"(\d(?:\.\d)?) out of 5 stars")


def parse_pasted_reviews(text, product):
    """Split text copied from an Amazon reviews page into reviews. Each review starts at 'N out of 5 stars'."""
    marks = list(STAR.finditer(text))
    items = []
    for i, m in enumerate(marks):
        chunk = text[m.start(): marks[i + 1].start() if i + 1 < len(marks) else len(text)]
        lines = [ln.strip() for ln in chunk.splitlines() if ln.strip()]
        head = STAR.sub("", lines[0]).strip() if lines else ""
        body_lines = [ln for ln in lines[1:] if not re.match(
            r"^(Reviewed in|Format:|Verified Purchase|Helpful|Report|Read more|Size:|Color:|\d+ (people|person)|One person)", ln)]
        # The reviewer's name usually sits on the last line of the previous chunk; it is dropped there.
        if body_lines and i + 1 < len(marks):
            body_lines = body_lines[:-1] if len(body_lines) > 1 and len(body_lines[-1]) < 40 else body_lines
        date = next((ln for ln in lines if ln.startswith("Reviewed in")), None)
        items.append(_review_item(product, None, f"pasted{i:03d}", float(m.group(1)), head or None,
                                  "\n".join(body_lines) or None, helpful_votes(chunk), date=date))
    return [it for it in items if it.get("text")]


def import_dir(root, log=print):
    items = []
    for d in sorted(p for p in pathlib.Path(root).iterdir() if p.is_dir()):
        product = d.name.replace("_", " ").replace("-", " ")
        rev = d / "reviews.txt"
        if rev.exists():
            got = parse_pasted_reviews(rev.read_text(errors="replace"), product)
            items += got
            log(f"  amazon pasted '{product}': {len(got)} reviews")
        lst = d / "listing.txt"
        if lst.exists():
            text = lst.read_text(errors="replace").strip()
            title = text.splitlines()[0][:200] if text else None
            items.append(_listing_item(product, None, title, text))
            log(f"  amazon pasted '{product}': listing copy")
    return items
