"""Render and save account briefs."""

import json
import re
from pathlib import Path

from acr import __version__


def render(d):
    """Render a research result as a Markdown brief."""
    s, gh = d["site"], d["github"]
    L = [f"# Account Brief: {d['domain']}", f"_Generated {d['date']} by acr v{__version__}_", ""]
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
    """Write the brief to out_dir as Markdown or JSON. Returns (path, content)."""
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    safe = re.sub(r"[^a-z0-9.-]", "_", d["domain"]) or "unknown"
    path = Path(out_dir) / f"{safe}.{'json' if as_json else 'md'}"
    content = json.dumps(d, indent=2, ensure_ascii=False) if as_json else render(d)
    path.write_text(content, encoding="utf-8")
    return path, content
