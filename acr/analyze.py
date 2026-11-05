"""Fetch a company homepage and extract GTM-relevant signals."""

import re
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from acr.fetch import get
from acr.signatures import load_ats, load_tech

_P = r"(?<![\w.-])(?:www\.)?"

SOCIAL = [
    ("LinkedIn", _P + r"linkedin\.com/(?:company|school)/[A-Za-z0-9_-]+"),
    ("X/Twitter", _P + r"(?:twitter|x)\.com/(?!share|intent|home|search|i/)[A-Za-z0-9_]{1,15}(?=[/?#\"'\s]|$)"),
    ("GitHub", _P + r"github\.com/(?!(?:sponsors|features|about|login|orgs|topics|marketplace|pricing|enterprise|settings)\b)[A-Za-z0-9_-]+"),
    ("YouTube", _P + r"youtube\.com/(?:@|channel/|c/|user/)[A-Za-z0-9_.-]+"),
    ("Instagram", _P + r"instagram\.com/(?!p/|explore)[A-Za-z0-9_.]+"),
]

PAGES = ["about", "careers", "jobs", "pricing", "blog", "customers"]


def clean_domain(raw):
    """Turn a URL or bare domain into a lowercase host without 'www.'."""
    raw = raw.strip()
    if "//" not in raw:
        raw = "https://" + raw
    return urlparse(raw).netloc.lower().removeprefix("www.")


def detect_stack(html, headers, tech):
    """Return (technology names, categories) found in the page HTML and headers."""
    low = html.lower().replace("\\/", "/")
    names, cats = set(), set()
    for t in tech:
        if any(sig in low for sig in t["signatures"]):
            names.add(t["name"])
            cats.add(t["category"])
    if "cloudflare" in str(headers.get("server", "")).lower() or "cf-ray" in headers:
        names.add("Cloudflare")
        cats.add("cdn")
    return sorted(names), sorted(cats)


def find_socials(html):
    """Return a dict of social profile URLs found anywhere in the HTML."""
    text = html.replace("\\/", "/")
    found = {}
    for label, pattern in SOCIAL:
        m = re.search(pattern, text)
        if m:
            found[label] = "https://" + m.group(0).removeprefix("www.").rstrip("/?#\"' ")
    return found


def detect_ats(html, ats):
    """Return the hiring platforms (Greenhouse, Lever...) referenced in the HTML."""
    low = html.lower()
    return sorted(name for name, sig in ats.items() if sig in low)


def check_page(home_url, name):
    """Return (name, exists, body). Rejects soft-404 pages that redirect elsewhere."""
    r = get(urljoin(home_url, "/" + name), retries=0)
    if r is None or r.status_code != 200:
        return name, False, ""
    ok = name in urlparse(r.url).path.lower()
    body = r.text if ok and name in ("careers", "jobs") else ""
    return name, ok, body


def analyze_site(domain):
    """Fetch the homepage and key pages. Returns a signals dict, or {'error': ...}."""
    r = None
    for host in (domain, "www." + domain):
        r = get(f"https://{host}")
        if r is not None and r.status_code < 400:
            break
    if r is None:
        return {"error": f"Could not reach {domain}"}
    if r.status_code >= 400:
        return {"error": f"{domain} returned HTTP {r.status_code} (site may block bots)"}
    if "html" not in r.headers.get("content-type", "").lower():
        return {"error": f"{domain} homepage is not HTML"}

    soup = BeautifulSoup(r.text, "html.parser")
    title = soup.title.get_text(strip=True) if soup.title else ""
    meta = soup.find("meta", attrs={"name": "description"}) or soup.find(
        "meta", attrs={"property": "og:description"}
    )
    desc = (meta.get("content") or "").strip() if meta else ""
    h1 = soup.find("h1")
    headline = h1.get_text(" ", strip=True)[:200] if h1 else ""

    stack, categories = detect_stack(r.text, r.headers, load_tech())

    with ThreadPoolExecutor(max_workers=6) as ex:
        checked = list(ex.map(lambda p: check_page(r.url, p), PAGES))
    pages = {name: ok for name, ok, _ in checked}
    jobs_html = " ".join(body for _, ok, body in checked if ok and body)

    return {
        "url": r.url,
        "title": title,
        "description": desc,
        "headline": headline,
        "stack": stack,
        "categories": categories,
        "socials": find_socials(r.text),
        "pages": pages,
        "ats": detect_ats(jobs_html, load_ats()),
    }
