"""Config and key loading. Keys live in .env at the project root (never in config/)."""
import os
import pathlib
import tomllib

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUTPUT = ROOT / "output"
INPUTS = ROOT / "inputs"

KEYS = {
    "SCRAPECREATORS_API_KEY": "Meta ad copy + transcripts, TikTok, Instagram, X, LinkedIn, live Reddit",
    "APIFY_TOKEN": "Amazon reviews and listing copy",
    "STACKEXCHANGE_KEY": "optional: raises the Stack Overflow quota from 300 to 10,000 calls a day",
}


def load_env(path=None):
    path = pathlib.Path(path or ROOT / ".env")
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k, v = k.strip(), v.strip().strip('"').strip("'")
        if v and k not in os.environ:
            os.environ[k] = v


def key(name):
    return os.environ.get(name) or None


def _merge(base, extra):
    """Lay `extra` over `base`: tables merge key by key, everything else is replaced."""
    for k, v in extra.items():
        if isinstance(v, dict) and isinstance(base.get(k), dict):
            _merge(base[k], v)
        else:
            base[k] = v
    return base


def load_config(path=None):
    """config/fanout.toml, with config/fanout.local.toml (git-ignored: competitor, channel and product
    names) laid over it when it exists."""
    path = pathlib.Path(path or ROOT / "config" / "fanout.toml")
    with open(path, "rb") as f:
        cfg = tomllib.load(f)
    local = path.with_name(path.stem + ".local.toml")
    if local.exists():
        with open(local, "rb") as f:
            _merge(cfg, tomllib.load(f))
    return cfg
