"""Playbooks: YAML rules that turn detected signals into outreach angles."""

from pathlib import Path

import yaml

DEFAULT_PLAYBOOKS = Path(__file__).parent / "playbooks"

COND_KEYS = {
    "has_tech",
    "has_all_tech",
    "lacks_tech",
    "has_category",
    "lacks_category",
    "has_page",
    "lacks_page",
    "hiring_platform",
    "github_min_repos",
    "github_language",
    "text_contains",
}


def as_list(value):
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        return [str(x).lower() for x in value]
    return [str(value).lower()]


def load_playbooks(path):
    """Return (rules, errors). path may be a .yml file or a folder of them."""
    rules, errors = [], []
    p = Path(path)
    if p.is_dir():
        files = sorted(list(p.glob("*.yml")) + list(p.glob("*.yaml")))
    elif p.exists():
        files = [p]
    else:
        return rules, [f"playbook path not found: {path}"]
    if not files:
        return rules, [f"no .yml files in {path}"]

    for f in files:
        try:
            data = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError as e:
            errors.append(f"{f.name}: invalid YAML ({str(e).splitlines()[0]})")
            continue
        if not isinstance(data, dict) or not isinstance(data.get("rules"), list):
            errors.append(f"{f.name}: needs a top-level 'rules:' list")
            continue
        pb_name = str(data.get("name") or f.stem)
        for i, rule in enumerate(data["rules"], 1):
            where = f"{f.name} rule #{i}"
            if not isinstance(rule, dict):
                errors.append(f"{where}: must be a mapping")
                continue
            if not rule.get("id") or not rule.get("angle"):
                errors.append(f"{where}: needs both 'id' and 'angle'")
                continue
            when = rule.get("when") or {}
            if not isinstance(when, dict):
                errors.append(f"{where} ({rule['id']}): 'when' must be a mapping")
                continue
            bad = set(when) - COND_KEYS
            if bad:
                errors.append(f"{where} ({rule['id']}): unknown condition {', '.join(sorted(bad))}")
                continue
            if "github_min_repos" in when:
                try:
                    int(when["github_min_repos"])
                except (TypeError, ValueError):
                    errors.append(f"{where} ({rule['id']}): github_min_repos must be a number")
                    continue
            rule = dict(rule)
            rule["when"] = when
            rule["playbook"] = pb_name
            rules.append(rule)
    return rules, errors


def match(when, site, gh):
    """True when every condition in a rule's 'when' block holds."""
    stack = {s.lower() for s in site["stack"]}
    cats = {c.lower() for c in site.get("categories", [])}
    pages = {p for p, ok in site["pages"].items() if ok}
    text = " ".join([site["title"], site["description"], site["headline"]]).lower()
    gh_ok = bool(gh) and "error" not in gh
    langs = {x.lower() for x in gh["languages"]} if gh_ok else set()

    for key, val in when.items():
        if key == "has_tech":
            ok = bool(stack & set(as_list(val)))
        elif key == "has_all_tech":
            ok = set(as_list(val)) <= stack
        elif key == "lacks_tech":
            ok = not (stack & set(as_list(val)))
        elif key == "has_category":
            ok = bool(cats & set(as_list(val)))
        elif key == "lacks_category":
            ok = not (cats & set(as_list(val)))
        elif key == "has_page":
            ok = bool(pages & set(as_list(val)))
        elif key == "lacks_page":
            ok = not (pages & set(as_list(val)))
        elif key == "hiring_platform":
            ok = bool(site["ats"]) == bool(val)
        elif key == "github_min_repos":
            ok = gh_ok and gh["public_repos"] >= int(val)
        elif key == "github_language":
            ok = bool(langs & set(as_list(val)))
        elif key == "text_contains":
            ok = any(w in text for w in as_list(val))
        else:
            ok = False
        if not ok:
            return False
    return True


def run_playbooks(domain, site, gh, rules):
    """Return matching rules as a list of dicts, highest priority first."""
    tm = "tag-manager" in site.get("categories", [])
    verify = " (tag manager detected, verify first)" if tm else " (homepage only, verify first)"
    hits = []
    for r in rules:
        if not match(r["when"], site, gh):
            continue
        text = str(r["angle"])
        text = text.replace("{domain}", domain)
        text = text.replace("{ats}", ", ".join(site["ats"]))
        text = text.replace("{stack}", ", ".join(site["stack"]))
        if r.get("verify"):
            text = text.rstrip(".") + verify + "."
        try:
            prio = int(r.get("priority", 0))
        except (TypeError, ValueError):
            prio = 0
        hits.append(
            {"id": str(r["id"]), "playbook": r["playbook"], "angle": text, "priority": prio}
        )
    hits.sort(key=lambda h: -h["priority"])
    return hits
