import pathlib
import time
import hashlib
import json
import requests
from bs4 import BeautifulSoup

CACHE_DIR = pathlib.Path("cache")
UA = {"User-Agent": "hlsl-specgen/0.1 (+python requests)"}


def ensure_dir(p: pathlib.Path):
    p.mkdir(parents=True, exist_ok=True)


def cache_path(url: str) -> pathlib.Path:
    ensure_dir(CACHE_DIR)
    h = hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]
    return CACHE_DIR / f"{h}.html"


def fetch(url: str, use_cache: bool = True, ttl_sec: int = 7*24*3600) -> str:
    """Fetch with dumb on-disk cache so your builds aren’t brittle."""
    cp = cache_path(url)
    if use_cache and cp.exists() and (time.time() - cp.stat().st_mtime) < ttl_sec:
        return cp.read_text(encoding="utf-8")
    html = requests.get(url, headers=UA, timeout=20).text
    cp.write_text(html, encoding="utf-8")
    return html


class Extractor:
    """Base class so every extractor exposes name/target_key/run()."""
    name = "base"
    target_key = ""

    def run(self):
        raise NotImplementedError


def to_soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "lxml")


def dedup_by_key(items, key="name"):
    seen, out = set(), []
    for it in items:
        k = it.get(key)
        if k and k not in seen:
            seen.add(k)
            out.append(it)
    return out


def merge_into(spec: dict, key: str, items: list[dict]):
    """Union by 'name' into spec[key]."""
    existing = {x["name"]: x for x in spec.get(key, []) if "name" in x}
    for it in items:
        nm = it.get("name")
        if not nm:
            continue
        if nm in existing:
            # shallow merge: keep old fields, add new ones if missing
            existing[nm].update({k: v for k, v in it.items(
            ) if k not in existing[nm] or existing[nm][k] in (None, [], "")})
        else:
            existing[nm] = it
    spec[key] = sorted(existing.values(), key=lambda x: x["name"].lower())


def write_to(path: pathlib.Path, data, *, indent: int = 2):
    """Overwrite `path` with `data`. If dict/list, JSON-dump; else write as text."""
    ensure_dir(path.parent)

    if isinstance(data, (dict, list)):
        text = json.dumps(data, indent=indent, ensure_ascii=False)
    else:
        text = str(data)

    # ensure trailing newline for nicer diffs
    if not text.endswith("\n"):
        text += "\n"

    path.write_text(text, encoding="utf-8")
