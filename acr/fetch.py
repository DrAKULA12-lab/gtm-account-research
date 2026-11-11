"""HTTP helper: polite user agent, timeout, a single retry and an optional URL guard."""

import threading
from urllib.parse import urljoin

import requests

from acr import __version__

UA = f"Mozilla/5.0 (compatible; GTMResearchBot/{__version__})"
TIMEOUT = 12

# Optional callable(url) -> bool. When set, every request and every redirect target
# must pass it. The MCP server uses this to keep AI agents away from private networks.
_url_guard = None

_local = threading.local()


def last_error():
    """Short reason the latest get() on this thread returned None ('' if none)."""
    return getattr(_local, "error", "")


def clear_error():
    """Forget the last error for this thread."""
    _local.error = ""


def _describe(exc):
    """Turn a requests exception into a short reason a person can act on."""
    if isinstance(exc, requests.exceptions.SSLError):
        return "SSL certificate problem"
    if isinstance(exc, requests.exceptions.Timeout):
        return "timed out"
    if isinstance(exc, requests.exceptions.TooManyRedirects):
        return "too many redirects"
    if isinstance(exc, requests.exceptions.InvalidURL) and "redirect blocked" in str(exc):
        return "redirected to a blocked address"
    if isinstance(exc, requests.exceptions.ConnectionError):
        return "could not connect (DNS or network problem)"
    return "request failed"


def set_url_guard(guard):
    """Install (or clear, with None) a function that decides whether a URL may be fetched."""
    global _url_guard
    _url_guard = guard


def _check_redirect(response, *args, **kwargs):
    """Requests hook: refuse to follow a redirect to a URL the guard rejects."""
    if _url_guard and response.is_redirect:
        target = urljoin(response.url, response.headers.get("location", ""))
        if not _url_guard(target):
            raise requests.exceptions.InvalidURL(f"redirect blocked: {target}")
    return response


def _get_network(url, headers=None, retries=1):
    """GET a URL. Returns a Response, or None if blocked or every attempt failed."""
    _local.error = ""
    if _url_guard and not _url_guard(url):
        _local.error = "blocked by the network safety guard"
        return None
    h = {"User-Agent": UA}
    if headers:
        h.update(headers)
    hooks = {"response": _check_redirect} if _url_guard else None
    for _ in range(retries + 1):
        try:
            return requests.get(
                url, headers=h, timeout=TIMEOUT, allow_redirects=True, hooks=hooks
            )
        except requests.RequestException as exc:
            _local.error = _describe(exc)
            continue
    return None


def get(url, headers=None, retries=1):
    """GET a URL, using the on-disk cache for plain public requests."""
    from acr import cache

    _local.error = ""
    if _url_guard and not _url_guard(url):
        _local.error = "blocked by the network safety guard"
        return None
    use_cache = not (
        headers and any(k.lower() == "authorization" for k in headers)
    )
    if use_cache:
        hit = cache.load(url)
        if hit is not None:
            return hit
    response = _get_network(url, headers=headers, retries=retries)
    if use_cache and response is not None and response.status_code == 200:
        cache.save(url, response)
    return response
