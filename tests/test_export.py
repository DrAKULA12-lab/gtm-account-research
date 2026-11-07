import csv

from acr.cli import main
from acr.export import COLUMNS, safe_cell, to_row, write_csv

OK = {
    "domain": "acme.com",
    "date": "2026-11-06",
    "site": {
        "title": "Acme",
        "description": "",
        "headline": "",
        "stack": ["HubSpot", "Next.js"],
        "categories": ["crm", "framework"],
        "socials": {},
        "pages": {"pricing": True, "careers": True, "blog": False},
        "ats": ["Lever"],
    },
    "github": {
        "name": "Acme",
        "public_repos": 12,
        "followers": 40,
        "last_push": "2026-11-01",
        "languages": ["Python"],
        "repos": [],
    },
    "angles": ["Hiring via Lever.", "Public pricing page."],
    "signals": [],
}

FAILED = {
    "domain": "down.example",
    "date": "2026-11-06",
    "site": {"error": "Could not reach down.example"},
    "github": None,
    "angles": [],
    "signals": [],
}


def test_safe_cell_blocks_formulas():
    assert safe_cell('=HYPERLINK("http://evil")') == "'=HYPERLINK(\"http://evil\")"
    assert safe_cell("+1 555") == "'+1 555"
    assert safe_cell("@SUM(A1)") == "'@SUM(A1)"
    assert safe_cell("Normal title") == "Normal title"
    assert safe_cell(None) == ""
    assert safe_cell("line one\nline two") == "line one line two"


def test_to_row_ok():
    row = to_row(OK)
    assert row["status"] == "ok"
    assert row["tech_stack"] == "HubSpot, Next.js"
    assert row["hiring_platform"] == "Lever"
    assert row["pages_found"] == "pricing, careers"
    assert row["github_repos"] == "12"
    assert row["angle_count"] == "2"
    assert row["top_angle"] == "Hiring via Lever."
    assert row["all_angles"] == "Hiring via Lever. | Public pricing page."


def test_to_row_error():
    row = to_row(FAILED)
    assert row["status"] == "error"
    assert row["error"] == "Could not reach down.example"
    assert row["top_angle"] == ""


def test_to_row_neutralizes_hostile_title():
    hostile = {**OK, "site": {**OK["site"], "title": "=cmd|' /C calc'!A0"}}
    assert to_row(hostile)["title"].startswith("'=")


def test_write_csv_roundtrip(tmp_path):
    path = write_csv([OK, FAILED], tmp_path / "out" / "summary.csv")
    with path.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    assert list(rows[0].keys()) == COLUMNS
    assert [r["domain"] for r in rows] == ["acme.com", "down.example"]
    assert rows[1]["status"] == "error"


def test_cli_writes_summary_csv(tmp_path, monkeypatch):
    fake = {"a.com": OK, "b.com": FAILED}
    monkeypatch.setattr("acr.cli.research", lambda dom, gh, rules: fake[dom])
    domains = tmp_path / "domains.txt"
    domains.write_text("a.com\nb.com\n")
    out = tmp_path / "briefs"
    main(["--file", str(domains), "--csv", "--out", str(out)])
    with (out / "summary.csv").open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 2
    assert (out / "acme.com.md").exists()
