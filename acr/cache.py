"""Small on-disk cache for fetched pages.

Settings (environment variables):
  ACR_NO_CACHE=1     turn the cache off
  ACR_CACHE_TTL=N    seconds to keep a page (default 86400 = 24 hours)
  ACR_CACHE_DIR=PATH where to store pages (default ~/.cache/acr)
"""
import base64
import hashlib
import json
import os
import threading
import time
from pathlib import Path

import requests
from requests.structures import CaseInsensitiveDict

DEFAULT_TTL = 24 * 60 * 60
MAX_BYTES = 2_000_000  # pages larger than this are not cached
_pruned = False


def enabled():
    return os.environ.get("ACR_NO_CACHE", "").lower() not in ("1", "true", "yes")


def _ttl():
    try:
        return int(os.environ.get("ACR_CACHE_TTL", DEFAULT_TTL))
    except ValueError:
        return DEFAULT_TTL


def _path(url):
    base = os.environ.get("ACR_CACHE_DIR")
    folder = Path(base) if base else Path.home() / ".cache" / "acr"
    name = hashlib.sha256(url.encode("utf-8")).hexdigest() + ".json"
    return folder / name


def load(url):
    """Return a cached Response for url, or None if missing or too old."""
    if not enabled():
        return None
    try:
        data = json.loads(_path(url).read_text(encoding="utf-8"))
        if time.time() - data["fetched_at"] > _ttl():
            return None
        response = requests.Response()
        response.status_code = data["status"]
        response.url = data["url"]
        response.encoding = data.get("encoding")
        response.headers = CaseInsensitiveDict(data.get("headers", {}))
        response._content = base64.b64decode(data["body"])
        response._content_consumed = True
        return response
    except (OSError, ValueError, KeyError):
        return None


def _prune(folder):
    """Delete entries older than the cache lifetime. Runs once per process."""
    global _pruned
    if _pruned:
        return
    _pruned = True
    cutoff = time.time() - _ttl()
    try:
        for f in folder.glob("*.json"):
            try:
                if f.stat().st_mtime < cutoff:
                    f.unlink()
            except OSError:
                pass
    except OSError:
        pass


def save(url, response):
    """Store a response on disk. Failures are ignored."""
    if not enabled() or len(response.content) > MAX_BYTES:
        return
    path = _path(url)
    _prune(path.parent)
    data = {
        "fetched_at": time.time(),
        "status": response.status_code,
        "url": response.url,
        "encoding": response.encoding,
        "headers": {"content-type": response.headers.get("content-type", "")},
        "body": base64.b64encode(response.content).decode("ascii"),
    }
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_name(f"{path.name}.{os.getpid()}.{threading.get_ident()}.tmp")
        tmp.write_text(json.dumps(data), encoding="utf-8")
        os.replace(tmp, path)
    except OSError:
        pass
