"""HTTP helper: polite user agent, timeout, a single retry and an optional URL guard."""

from urllib.parse import urljoin

import requests

from acr import __version__

UA = f"Mozilla/5.0 (compatible; GTMResearchBot/{__version__})"
TIMEOUT = 12

# Optional callable(url) -> bool. When set, every request and every redirect target
# must pass it. The MCP server uses this to keep AI agents away from private networks.
_url_guard = None


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


def get(url, headers=None, retries=1):
    """GET a URL. Returns a Response, or None if blocked or every attempt failed."""
    if _url_guard and not _url_guard(url):
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
        except requests.RequestException:
            continue
    return None
