#!/usr/bin/env python3
"""GTM Account Research Agent v0.2

Usage:
  python acr.py stripe.com
  python acr.py stripe.com --github stripe
  python acr.py --file domains.txt --json
"""

import argparse
import json
import os
import re
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

VERSION = "0.2"
UA = "Mozilla/5.0 (compatible; GTMResearchBot/0.2)"
TIMEOUT = 12

TECH = {
    "HubSpot": ["js.hs-scripts.com", "js.hsforms.net", "hs-analytics.net"],
    "Salesforce/Pardot": ["pardot.com", "pi.pardot", "force.com"],
    "Marketo": ["munchkin.marketo.net", "mktoforms"],
    "Intercom": ["widget.intercom.io", "intercomsettings"],
    "Drift": ["js.driftt.com", "drift.com/include"],
    "Zendesk": ["static.zdassets.com", "zendesk.com/embeddable"],
    "Crisp": ["client.crisp.chat"],
    "Segment": ["cdn.segment.com"],
    "Mixpanel": ["cdn.mxpnl.com", "mixpanel.com/"],
    "Amplitude": ["cdn.amplitude.com", "amplitude.com/libs"],
    "PostHog": ["posthog.init", "i.posthog.com"],
    "Hotjar": ["static.hotjar.com"],
    "Google Analytics/GTM": ["googletagmanager.com", "google-analytics.com"],
    "Meta Pixel": ["connect.facebook.net", "fbq("],
    "LinkedIn Insight": ["snap.licdn.com"],
    "Stripe": ["js.stripe.com"],
    "Shopify": ["cdn.shopify.com"],
    "WordPress": ["wp-content", "wp-includes"],
    "Webflow": ["data-wf-page", "assets.website-files.com"],
    "Next.js": ["/_next/", "__next_data__"],
    "Calendly": ["assets.calendly.com", "calendly.com/"],
    "Typeform": ["embed.typeform.com"],
}

CHAT = {"Intercom", "Drift", "Zendesk", "Crisp"}
CRM = {"HubSpot", "Salesforce/Pardot", "Marketo"}
ANALYTICS = {"Segment", "Mixpanel", "Amplitude", "PostHog"}

ATS = {
    "Greenhouse": "greenhouse.io",
    "Lever": "lever.co",
    "Ashby": "ashbyhq.com",
    "Workable": "workable.com",
    "SmartRecruiters": "smartrecruiters.com",
    "BambooHR": "bamboohr.com",
    "Workday": "myworkdayjobs.com",
}

SOCIAL = [
    ("LinkedIn", r"linkedin\.com/(?:company|school)/[A-Za-z0-9_-]+"),
    ("X/Twitter", r"(?:twitter|x)\.com/(?!share|intent|home|search|i/)[A-Za-z0-9_]{1,15}(?=[/?#\"'\s]|$)"),
    ("GitHub", r"github\.com/(?!(?:sponsors|features|about|login|orgs|topics|marketplace|pricing|enterprise|settings)\b)[A-Za-z0-9_-]+"),
    ("YouTube", r"youtube\.com/(?:@|channel/|c/|user/)[A-Za-z0-9_.-]+"),
    ("Instagram", r"instagram\.com/(?!p/|explore)[A-Za-z0-9_.]+"),
]

PAGES = ["about", "careers", "jobs", "pricing", "blog", "customers"]


def get(url, headers=None, retries=1):
    h = {"User-Agent": UA}
    if headers:
        h.update(headers)
    for _ in range(retries + 1):
        try:
            return requests.get(url, headers=h, timeout=TIMEOUT, allow_redirects=True)
        except requests.RequestException:
            continue
    return None


def clean_domain(raw):
    raw = raw.strip()
    if "//" not in raw:
        raw = "https://" + raw
    return urlparse(raw).netloc.lower().removeprefix("www.")


def check_page(home_url, name):
    """Return (name, exists, body). Rejects soft-404 pages that redirect elsewhere."""
    r = get(urljoin(home_url, "/" + name), retries=0)
    if r is None or r.status_code != 200:
        return name, False, ""
    ok = name in urlparse(r.url).path.lower()
    body = r.text if ok and name in ("careers", "jobs") else ""
    return name, ok, body


def analyze_site(domain):
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

    text = r.text
    low = text.lower().replace("\\/", "/")
    soup = BeautifulSoup(text, "html.parser")

    title = soup.title.get_text(strip=True) if soup.title else ""
    meta = soup.find("meta", attrs={"name": "description"}) or soup.find(
        "meta", attrs={"property": "og:description"}
    )
    desc = (meta.get("content") or "").strip() if meta else ""
    h1 = soup.find("h1")
    headline = h1.get_text(" ", strip=True)[:200] if h1 else ""

    stack = {n for n, sigs in TECH.items() if any(s in low for s in sigs)}
    server = r.headers.get("server", "").lower()
    if "cloudflare" in server or "cf-ray" in r.headers:
        stack.add("Cloudflare")

    socials = {}
    clean_text = text.replace("\\/", "/")
    for label, pattern in SOCIAL:
        m = re.search(pattern, clean_text)
        if m:
            socials[label] = "https://" + m.group(0).rstrip("/?#\"' ")

    with ThreadPoolExecutor(max_workers=6) as ex:
        checked = list(ex.map(lambda p: check_page(r.url, p), PAGES))
    pages = {name: ok for name, ok, _ in checked}
    jobs_html = " ".join(body for _, ok, body in checked if ok and body).lower()
    ats = sorted(n for n, sig in ATS.items() if sig in jobs_html)

    return {
        "url": r.url,
        "title": title,
        "description": desc,
        "headline": headline,
        "stack": sorted(stack),
        "socials": socials,
        "pages": pages,
        "ats": ats,
    }


def github_info(name):
    headers = {"Accept": "application/vnd.github+json"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    r = get(f"https://api.github.com/users/{name}", headers)
    if r is None:
        return {"error": "GitHub unreachable"}
    if r.status_code in (403, 429):
        return {"error": "GitHub rate limit hit. Set GITHUB_TOKEN to raise the limit."}
    if r.status_code != 200:
        return {"error": f"GitHub account '{name}' not found"}
    u = r.json()
    kind = "orgs" if u.get("type") == "Organization" else "users"
    rr = get(
        f"https://api.github.com/{kind}/{name}/repos?sort=pushed&per_page=30", headers
    )
    repos = rr.json() if rr is not None and rr.status_code == 200 else []
    own = [x for x in repos if not x.get("fork")]
    top = sorted(own, key=lambda x: x["stargazers_count"], reverse=True)[:5]
    langs = Counter(x["language"] for x in own if x.get("language"))
    pushed = [x["pushed_at"] for x in own if x.get("pushed_at")]
    return {
        "name": u.get("name") or name,
        "public_repos": u.get("public_repos", 0),
        "followers": u.get("followers", 0),
        "last_push": max(pushed)[:10] if pushed else None,
        "languages": [l for l, _ in langs.most_common(3)],
        "repos": [
            {
                "name": x["name"],
                "stars": x["stargazers_count"],
                "lang": x.get("language") or "-",
                "url": x["html_url"],
            }
            for x in top
        ],
    }


def outreach_angles(site, gh):
    s = set(site["stack"])
    pages = site["pages"]
    tm = "Google Analytics/GTM" in s
    verify = (
        " (tag manager detected, verify first)" if tm else " (homepage only, verify first)"
    )
    out = []
    if site["ats"]:
        out.append(f"Hiring via {', '.join(site['ats'])}: open roles are a growth signal, reference them.")
    elif pages.get("careers") or pages.get("jobs"):
        out.append("Careers page is live: check open roles as a growth signal.")
    if pages.get("pricing"):
        out.append("Public pricing page: self-serve motion, lead with time-to-value.")
    if pages.get("customers"):
        out.append("Public customer page: reference a similar customer story.")
    if s & ANALYTICS:
        out.append("Product analytics in place: data-driven team, lead with metrics.")
    if not s & CHAT:
        out.append("No chat widget in homepage HTML: possible inbound gap" + verify + ".")
    if not s & CRM:
        out.append("No CRM/marketing tag in homepage HTML: tooling may be early" + verify + ".")
    if gh and "error" not in gh and gh["public_repos"] > 0:
        out.append("Public GitHub presence: developer-led motion, technical outreach can land.")
    return out or ["No strong signals found: open with a generic value-first message."]


def research(domain_raw, gh_name=None):
    domain = clean_domain(domain_raw)
    if "." in domain:
        site = analyze_site(domain)
    else:
        site = {"error": f"'{domain_raw}' is not a valid domain"}
    if not gh_name and "error" not in site:
        gh_name = site["socials"].get("GitHub", "").rsplit("/", 1)[-1] or None
    gh = github_info(gh_name) if gh_name else None
    angles = outreach_angles(site, gh) if "error" not in site else []
    return {
        "domain": domain,
        "date": str(date.today()),
        "site": site,
        "github": gh,
        "angles": angles,
    }


def render(d):
    s, gh = d["site"], d["github"]
    L = [f"# Account Brief: {d['domain']}", f"_Generated {d['date']} by acr v{VERSION}_", ""]
    if "error" in s:
        return "\n".join(L + [f"**Error:** {s['error']}"]) + "\n"

    L += [
        "## Overview",
        f"- **Title:** {s['title'] or '-'}",
        f"- **Description:** {s['description'] or '-'}",
    ]
    if s["headline"]:
        L.append(f"- **Headline:** {s['headline']}")

    L += ["", "## Detected Tech Stack", ", ".join(s["stack"]) or "Nothing detected."]
    L += ["", "## Social Links"]
    L += [f"- {k}: {v}" for k, v in s["socials"].items()] or ["None found."]
    L += ["", "## Pages Found", ", ".join(p for p, ok in s["pages"].items() if ok) or "None."]

    if s["ats"]:
        L += ["", "## Hiring", "Applicant tracking: " + ", ".join(s["ats"])]

    if gh:
        L += ["", "## GitHub"]
        if "error" in gh:
            L.append(f"- {gh['error']}")
        else:
            L.append(
                f"- {gh['name']}: {gh['public_repos']} public repos, "
                f"{gh['followers']} followers, last push {gh['last_push'] or '-'}"
            )
            if gh["languages"]:
                L.append("- Top languages: " + ", ".join(gh["languages"]))
            L += [
                f"  - [{x['name']}]({x['url']}) ({x['lang']}, {x['stars']} stars)"
                for x in gh["repos"]
            ]

    L += ["", "## Suggested Outreach Angles"] + [f"- {a}" for a in d["angles"]]
    L += [
        "",
        "> Signals come from public homepage HTML and the GitHub API. "
        "Treat gaps as hints to verify, not facts.",
    ]
    return "\n".join(L) + "\n"


def save(d, out_dir, as_json):
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    safe = re.sub(r"[^a-z0-9.-]", "_", d["domain"]) or "unknown"
    path = Path(out_dir) / f"{safe}.{'json' if as_json else 'md'}"
    content = json.dumps(d, indent=2, ensure_ascii=False) if as_json else render(d)
    path.write_text(content, encoding="utf-8")
    return path, content


def parse_file(path):
    items = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        dom, _, gh = line.partition(",")
        items.append((dom.strip(), gh.strip() or None))
    return items


def main():
    ap = argparse.ArgumentParser(description="GTM account research brief")
    ap.add_argument("domain", nargs="?", help="e.g. stripe.com")
    ap.add_argument("--github", help="GitHub org/user (auto-detected if omitted)")
    ap.add_argument("--file", help="text file, one 'domain' or 'domain,github' per line")
    ap.add_argument("--json", action="store_true", help="write JSON instead of Markdown")
    ap.add_argument("--out", default="briefs", help="output folder")
    ap.add_argument("--version", action="version", version=f"acr {VERSION}")
    args = ap.parse_args()

    targets = []
    if args.file:
        if not Path(args.file).exists():
            ap.error(f"file not found: {args.file}")
        targets = parse_file(args.file)
    if args.domain:
        targets.insert(0, (args.domain, args.github))
    if not targets:
        ap.error("give a domain or --file")

    print(f"[*] Researching {len(targets)} account(s) ...")
    with ThreadPoolExecutor(max_workers=3) as ex:
        results = list(ex.map(lambda t: research(*t), targets))

    for d in results:
        path, content = save(d, args.out, args.json)
        if len(results) == 1:
            print(content)
        status = "ERR" if "error" in d["site"] else "OK"
        print(f"[{status}] {d['domain']} -> {path}")


if __name__ == "__main__":
    main()
