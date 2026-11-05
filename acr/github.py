"""GitHub public API lookups for an organization or user."""

import os
from collections import Counter

from acr.fetch import get


def github_info(name):
    """Return a summary of a GitHub org/user, or {'error': ...}."""
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
    rr = get(f"https://api.github.com/{kind}/{name}/repos?sort=pushed&per_page=30", headers)
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
        "languages": [lang for lang, _ in langs.most_common(3)],
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
