"""Parse the text of a public Meta Ad Library advertiser page (read in the built-in browser).

Open, for each competitor:
  https://www.facebook.com/ads/library/?active_status=all&ad_type=all&country=ALL
      &view_all_page_id=<PAGE_ID>&sort_data[mode]=total_impressions&sort_data[direction]=desc
      &search_type=page&media_type=all
and save the page text. Sorted by impressions, it shows the ads the advertiser has spent most on,
with run dates (active and stopped), "N ads use this creative and text", video length and full copy.
"""
import datetime as dt
import re
import time

from ..store import make_item

DATE = r"(\d{1,2} [A-Z][a-z]{2,8} \d{4}|[A-Z][a-z]{2,8} \d{1,2}, \d{4})"
VIDEO = re.compile(r"^\d+:\d{2} / (\d+):(\d{2})$")
DOMAIN = re.compile(r"^[A-Z0-9][A-Z0-9.-]*\.[A-Z]{2,}$")
CTAS = {"Subscribe", "Learn more", "Sign up", "Shop now", "Download", "Apply now", "Book now", "Get offer",
        "Watch more", "Visit Instagram profile", "Send message", "Register", "Get quote", "Contact us",
        "Install now", "Use app", "Listen now", "Order now", "Get started", "Join now", "See more",
        "Send WhatsApp message", "Get access", "Enrol now", "Enroll now", "Request time", "Watch video"}
STOP = {"See more", "System status"}
CTAS_L = {c.lower() for c in CTAS}


def _is_cta(line):
    return line.lower() in CTAS_L


def _date(s):
    for fmt in ("%d %b %Y", "%d %B %Y", "%b %d, %Y", "%B %d, %Y"):
        try:
            return int(dt.datetime.strptime(s, fmt).replace(tzinfo=dt.timezone.utc).timestamp())
        except ValueError:
            continue
    return None


def parse(text, page_id=None, now_ts=None):
    now_ts = now_ts or int(time.time())
    text = text.replace("​", "")
    if not page_id:
        m = re.search(r"view_all_page_id=(\d+)", text)
        page_id = m.group(1) if m else None
    parts = re.split(r"Library ID: (\d+)", text)
    items = []
    for i in range(1, len(parts) - 1, 2):
        ad_id, seg = parts[i], parts[i + 1]
        prev = [ln.strip() for ln in parts[i - 1].splitlines() if ln.strip()]
        active = bool(prev) and prev[-1] == "Active"
        lines = [ln.strip() for ln in seg.splitlines()]
        while lines and lines[-1] in ("", "Active", "Inactive"):
            lines.pop()
        start = end = None
        m = re.search(r"Started running on " + DATE, seg)
        m2 = re.search(DATE + r"\s*[-–]\s*" + DATE, seg)
        if m:
            start = _date(m.group(1))
        elif m2:
            start, end = _date(m2.group(1)), _date(m2.group(2))
        mv = re.search(r"(\d+) ads use this creative and text", seg)
        listed = int(mv.group(1)) if mv else 1
        page_name, body, tail = None, [], []
        if "Sponsored" in lines:
            k = lines.index("Sponsored")
            page_name = next((ln for ln in reversed(lines[:k]) if ln), None)
            rest = lines[k + 1:]
            for j, ln in enumerate(rest):
                if VIDEO.match(ln) or DOMAIN.match(ln) or ln in STOP:
                    tail = rest[j:]
                    break
                body.append(ln)
        # a closing CTA button with no domain/video line before it: peel CTA + headline lines off the body
        while body and not body[-1]:
            body.pop()
        if body and _is_cta(body[-1]):
            tail = body[-3:] + tail if len(body) >= 3 and all(len(x) < 70 for x in body[-3:]) else body[-1:] + tail
            body = body[: len(body) - (3 if len(body) >= 3 and all(len(x) < 70 for x in body[-3:]) else 1)]
        video_s = None
        for ln in tail + lines:
            vm = VIDEO.match(ln)
            if vm:
                video_s = int(vm.group(1)) * 60 + int(vm.group(2))
                break
        tail = [ln for ln in tail if ln and not VIDEO.match(ln) and not DOMAIN.match(ln) and ln not in STOP]
        cta = next((ln for ln in tail if _is_cta(ln)), None)
        headline = next((ln for ln in tail if not _is_cta(ln)), None)
        days = max(0, ((now_ts if active else (end or start)) - start) // 86400) if start else None
        copy = "\n".join(body).strip() or None
        items.append(make_item(
            "ads", "meta_ads", ad_id,
            url=f"https://www.facebook.com/ads/library/?id={ad_id}",
            author=page_name, title=headline, text=copy,
            published_at=dt.datetime.fromtimestamp(start, dt.timezone.utc).date().isoformat() if start else None,
            metrics={"days_active": days, "is_active": active, "start_ts": start, "end_ts": end,
                     "variants_listed": listed, "video_s": video_s},
            extra={"provider": "adlibrary_page", "page_id": page_id or "", "cta": cta,
                   "format": "video" if video_s else "image/other",
                   "multiple_versions": "This ad has multiple versions" in seg},
        ))
    return items
