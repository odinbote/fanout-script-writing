"""SQLite swipe file. One row per collected item (ad, video, post, review), across all four methods."""
import datetime as dt
import json
import sqlite3

from .config import DATA

PILLARS = ("ads", "organic", "community", "marketplace")

SCHEMA = """
CREATE TABLE IF NOT EXISTS items (
  id TEXT PRIMARY KEY,
  pillar TEXT NOT NULL,
  source TEXT NOT NULL,
  url TEXT,
  author TEXT,
  title TEXT,
  text TEXT,
  transcript TEXT,
  published_at TEXT,
  first_seen_at TEXT,
  collected_at TEXT,
  query TEXT,
  metrics TEXT,
  extra TEXT,
  score REAL,
  grade TEXT
);
CREATE INDEX IF NOT EXISTS ix_items_pillar ON items(pillar, score DESC);
"""


def now_iso():
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def ts_to_iso(ts):
    if ts in (None, "", 0, "0"):
        return None
    try:
        return dt.datetime.fromtimestamp(int(float(ts)), dt.timezone.utc).replace(microsecond=0).isoformat()
    except (TypeError, ValueError, OSError):
        return None


def make_item(pillar, source, native_id, **fields):
    assert pillar in PILLARS, pillar
    item = {
        "id": f"{source}:{native_id}",
        "pillar": pillar,
        "source": source,
        "url": None, "author": None, "title": None, "text": None, "transcript": None,
        "published_at": None, "query": None,
        "metrics": {}, "extra": {},
    }
    item.update({k: v for k, v in fields.items() if v is not None})
    return item


def connect(path=None):
    DATA.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path or DATA / "pipeline.db")
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def _longer(a, b):
    a, b = a or "", b or ""
    return (b if len(b) > len(a) else a) or None


def upsert(conn, items):
    stamp = now_iso()
    n_new = 0
    for it in items:
        row = conn.execute("SELECT * FROM items WHERE id=?", (it["id"],)).fetchone()
        if row is None:
            n_new += 1
            conn.execute(
                "INSERT INTO items (id,pillar,source,url,author,title,text,transcript,published_at,first_seen_at,"
                "collected_at,query,metrics,extra) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (it["id"], it["pillar"], it["source"], it.get("url"), it.get("author"), it.get("title"),
                 it.get("text"), it.get("transcript"), it.get("published_at"), stamp, stamp, it.get("query"),
                 json.dumps(it.get("metrics") or {}), json.dumps(it.get("extra") or {})),
            )
            continue
        metrics = json.loads(row["metrics"] or "{}")
        metrics.update({k: v for k, v in (it.get("metrics") or {}).items() if v is not None})
        extra = json.loads(row["extra"] or "{}")
        # a re-parse from the same provider replaces its own text; other providers keep the longer one
        same = bool(extra.get("provider")) and extra.get("provider") == (it.get("extra") or {}).get("provider")
        new_text = it.get("text") if (same and it.get("text")) else _longer(row["text"], it.get("text"))
        extra.update({k: v for k, v in (it.get("extra") or {}).items() if v is not None})
        queries = {q for q in (row["query"] or "").split(" | ") if q}
        if it.get("query"):
            queries.add(it["query"])
        conn.execute(
            "UPDATE items SET url=COALESCE(?,url), author=COALESCE(?,author), title=COALESCE(?,title), text=?,"
            " transcript=?, published_at=COALESCE(?,published_at), collected_at=?, query=?, metrics=?, extra=?"
            " WHERE id=?",
            (it.get("url"), it.get("author"), it.get("title"), new_text,
             _longer(row["transcript"], it.get("transcript")), it.get("published_at"), stamp,
             " | ".join(sorted(queries)) or None, json.dumps(metrics), json.dumps(extra), it["id"]),
        )
    conn.commit()
    return n_new


def _row(r):
    d = dict(r)
    d["metrics"] = json.loads(d["metrics"] or "{}")
    d["extra"] = json.loads(d["extra"] or "{}")
    return d


def fetch(conn, pillar=None, source=None, order_by_score=False):
    sql, args = "SELECT * FROM items WHERE 1=1", []
    if pillar:
        sql += " AND pillar=?"
        args.append(pillar)
    if source:
        sql += " AND source=?"
        args.append(source)
    if order_by_score:
        sql += " ORDER BY score DESC"
    return [_row(r) for r in conn.execute(sql, args)]


def get(conn, item_id):
    r = conn.execute("SELECT * FROM items WHERE id=?", (item_id,)).fetchone()
    return _row(r) if r else None


def set_scores(conn, rows):
    conn.executemany("UPDATE items SET score=?, grade=? WHERE id=?", [(s, g, i) for i, s, g in rows])
    conn.commit()


def set_metrics(conn, items):
    conn.executemany("UPDATE items SET metrics=?, extra=? WHERE id=?",
                     [(json.dumps(i["metrics"]), json.dumps(i["extra"]), i["id"]) for i in items])
    conn.commit()


def set_text(conn, item_id, text=None, transcript=None):
    if text is not None:
        conn.execute("UPDATE items SET text=? WHERE id=?", (text, item_id))
    if transcript is not None:
        conn.execute("UPDATE items SET transcript=? WHERE id=?", (transcript, item_id))
    conn.commit()
