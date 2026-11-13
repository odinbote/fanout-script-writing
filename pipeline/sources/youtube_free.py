"""YouTube without a key, through the yt-dlp CLI: channel shorts/videos with view counts, keyword
search, and captions for transcripts."""
import json
import pathlib
import subprocess
import tempfile

from ..store import make_item
from .scrapecreators import vtt_to_text


def _ytdlp(args, timeout=240):
    r = subprocess.run(["yt-dlp", "--ignore-config", "--no-warnings", *args], capture_output=True, text=True,
                       timeout=timeout)
    if r.returncode != 0:
        raise RuntimeError((r.stderr or r.stdout).strip().splitlines()[-1] if (r.stderr or r.stdout) else "yt-dlp failed")
    return r.stdout


def _entry_item(e, query, channel=None, kind=None):
    vid = e.get("id")
    if kind is None:
        dur = e.get("duration")
        kind = "short" if ("/shorts/" in (e.get("url") or "") or (dur and dur <= 75)) else "video"
    return make_item(
        "organic", "youtube", vid,
        url=f"https://www.youtube.com/watch?v={vid}" if "shorts" not in (e.get("url") or "") else e.get("url"),
        author=channel or e.get("channel") or e.get("uploader"),
        title=e.get("title"), text=e.get("description") or None, query=query,
        metrics={"views": e.get("view_count"), "duration_s": e.get("duration")},
        extra={"channel_id": e.get("channel_id"), "kind": kind},
    )


def channel(handle, kind="shorts", n=40):
    out = _ytdlp(["--flat-playlist", "-J", "--playlist-end", str(n), f"https://www.youtube.com/@{handle}/{kind}"])
    d = json.loads(out)
    name = d.get("channel") or d.get("uploader") or handle
    k = "short" if kind == "shorts" else "video"
    return [_entry_item(e, f"account:{handle}", channel=name, kind=k) for e in d.get("entries") or [] if e.get("id")]


def search(query, n=25):
    d = json.loads(_ytdlp(["--flat-playlist", "-J", f"ytsearch{n}:{query}"]))
    return [_entry_item(e, f"search:{query}") for e in d.get("entries") or [] if e.get("id")]


def collect(cfg, log=print, out=None):
    o = cfg["organic"]
    items = [] if out is None else out  # out may save each batch as it arrives
    for h in o.get("youtube_channels", []):
        for kind in ("shorts", "videos"):
            try:
                got = channel(h, kind, o.get("videos_per_channel", 40))
            except Exception as e:  # noqa: BLE001 - a bad handle should not stop the run
                log(f"  ! youtube @{h}/{kind}: {e}")
                continue
            items += got
            log(f"  youtube @{h}/{kind}: {len(got)}")
    for term in o.get("search_terms", []):
        try:
            got = search(term)
        except Exception as e:  # noqa: BLE001
            log(f"  ! youtube search '{term}': {e}")
            continue
        items += got
        log(f"  youtube search '{term}': {len(got)}")
    return items


def transcript(video_url):
    with tempfile.TemporaryDirectory() as tmp:
        try:
            _ytdlp(["--skip-download", "--write-subs", "--write-auto-subs", "--sub-langs", "en,en-orig,en-US,en-GB",
                    "--sleep-subtitles", "3", "--sub-format", "vtt", "-o", f"{tmp}/%(id)s.%(ext)s", video_url],
                   timeout=180)
        except Exception:  # noqa: BLE001
            return None
        files = sorted(pathlib.Path(tmp).glob("*.vtt"), key=lambda p: ("orig" in p.name, len(p.name)))
        return vtt_to_text(files[0].read_text(errors="replace")) if files else None
