"""Small HTTP helpers (stdlib only). Identifies itself honestly; keys go in headers, never in URLs."""
import gzip
import json
import time
import urllib.error
import urllib.parse
import urllib.request

UA = "fanout-script-pipeline/0.1"


class FetchError(Exception):
    pass


def _url(url, params):
    if not params:
        return url
    clean = {k: v for k, v in params.items() if v is not None and v != ""}
    return url + ("&" if "?" in url else "?") + urllib.parse.urlencode(clean, doseq=True)


def _read(resp):
    raw = resp.read()
    if resp.headers.get("Content-Encoding") == "gzip":
        raw = gzip.decompress(raw)
    return raw.decode("utf-8", errors="replace")


def request_json(url, params=None, headers=None, body=None, timeout=90, retries=3, backoff=4.0):
    full = _url(url, params)
    hdrs = {"User-Agent": UA, "Accept": "application/json", "Accept-Encoding": "gzip"}
    hdrs.update(headers or {})
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        hdrs["Content-Type"] = "application/json"
    last = None
    for attempt in range(retries):
        req = urllib.request.Request(full, headers=hdrs, data=data, method="POST" if data else "GET")
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(_read(resp))
        except urllib.error.HTTPError as e:
            detail = e.read()[:300].decode("utf-8", errors="replace")
            last = f"HTTP {e.code}: {detail}"
            if e.code in (408, 429, 500, 502, 503, 504) and attempt < retries - 1:
                time.sleep(backoff * (attempt + 1))
                continue
            raise FetchError(f"{url.split('?')[0]} -> {last}") from None
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
            last = repr(e)
            if attempt < retries - 1:
                time.sleep(backoff * (attempt + 1))
    raise FetchError(f"{url.split('?')[0]} -> {last}")
