"""Orchestration: research one account end to end."""

from datetime import date

from acr.analyze import analyze_site, clean_domain
from acr.github import github_info
from acr.playbooks import run_playbooks


def research(domain_raw, gh_name=None, rules=None):
    """Analyze a domain (and its GitHub org) and apply playbook rules."""
    domain = clean_domain(domain_raw)
    if "." in domain:
        site = analyze_site(domain)
    else:
        site = {"error": f"'{domain_raw}' is not a valid domain"}
    if not gh_name and "error" not in site:
        gh_name = site["socials"].get("GitHub", "").rsplit("/", 1)[-1] or None
    gh = github_info(gh_name) if gh_name else None

    angles, signals = [], []
    if "error" not in site:
        hits = run_playbooks(domain, site, gh, rules or [])
        angles = [h["angle"] for h in hits]
        signals = [{"id": h["id"], "playbook": h["playbook"]} for h in hits]
        if not angles:
            angles = ["No rules matched: open with a generic value-first message."]

    return {
        "domain": domain,
        "date": str(date.today()),
        "site": site,
        "github": gh,
        "angles": angles,
        "signals": signals,
    }
