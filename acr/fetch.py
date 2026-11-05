"""HTTP helper: polite user agent, timeout and a single retry."""

import requests

from acr import __version__

UA = f"Mozilla/5.0 (compatible; GTMResearchBot/{__version__})"
TIMEOUT = 12


def get(url, headers=None, retries=1):
    """GET a URL. Returns a Response, or None if every attempt failed."""
    h = {"User-Agent": UA}
    if headers:
        h.update(headers)
    for _ in range(retries + 1):
        try:
            return requests.get(url, headers=h, timeout=TIMEOUT, allow_redirects=True)
        except requests.RequestException:
            continue
    return None
