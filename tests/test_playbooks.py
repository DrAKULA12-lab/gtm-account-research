from acr.core import research
from acr.playbooks import DEFAULT_PLAYBOOKS, load_playbooks, run_playbooks
from acr.report import render

SITE = {
    "url": "https://acme.com/",
    "title": "Acme",
    "description": "",
    "headline": "",
    "stack": ["Next.js"],
    "categories": ["framework"],
    "socials": {},
    "pages": {"pricing": True, "careers": False},
    "ats": ["Lever"],
}


def test_default_playbooks_are_valid():
    rules, errors = load_playbooks(DEFAULT_PLAYBOOKS)
    assert errors == []
    assert len(rules) >= 8


def test_rules_fire_and_fill_placeholders():
    rules, _ = load_playbooks(DEFAULT_PLAYBOOKS)
    hits = run_playbooks("acme.com", SITE, None, rules)
    ids = {h["id"] for h in hits}
    assert {"hiring-ats", "pricing-public", "no-chat", "no-crm"} <= ids
    assert any("Lever" in h["angle"] for h in hits)


def test_priority_order():
    rules, _ = load_playbooks(DEFAULT_PLAYBOOKS)
    prios = [h["priority"] for h in run_playbooks("acme.com", SITE, None, rules)]
    assert prios == sorted(prios, reverse=True)


def test_invalid_playbook_reports_errors(tmp_path):
    bad = tmp_path / "bad.yml"
    bad.write_text("rules:\n  - id: x\n    when:\n      nope: 1\n    angle: hi\n")
    rules, errors = load_playbooks(bad)
    assert rules == []
    assert any("unknown condition" in e for e in errors)


def test_custom_rule_with_domain_placeholder(tmp_path):
    custom = tmp_path / "mine.yml"
    custom.write_text(
        "name: Mine\nrules:\n  - id: a\n    when:\n      has_page: [pricing]\n"
        "    angle: 'Hello {domain}'\n    priority: 99\n"
    )
    rules, errors = load_playbooks(custom)
    assert errors == []
    assert run_playbooks("acme.com", SITE, None, rules)[0]["angle"] == "Hello acme.com"


def test_research_and_render(monkeypatch):
    monkeypatch.setattr("acr.core.analyze_site", lambda domain: dict(SITE))
    rules, _ = load_playbooks(DEFAULT_PLAYBOOKS)
    result = research("https://www.acme.com", rules=rules)
    assert result["domain"] == "acme.com"
    assert result["angles"] and result["signals"]
    assert "# Account Brief: acme.com" in render(result)


def test_invalid_domain():
    result = research("not-a-domain")
    assert "error" in result["site"]
