from acr.analyze import analyze_site, clean_domain, detect_ats, detect_stack, find_socials
from acr.signatures import load_ats, load_tech


class FakeResponse:
    def __init__(self, text="", status=200, url="", headers=None):
        self.text = text
        self.status_code = status
        self.url = url
        self.headers = headers or {"content-type": "text/html"}


def test_clean_domain():
    assert clean_domain("https://www.Stripe.com/pricing") == "stripe.com"
    assert clean_domain("stripe.com") == "stripe.com"


def test_detect_stack_and_categories():
    html = (
        '<script src="https://js.hs-scripts.com/1.js"></script>'
        '<script src="https://widget.intercom.io/widget/abc"></script>'
    )
    names, cats = detect_stack(html, {}, load_tech())
    assert "HubSpot" in names and "Intercom" in names
    assert {"crm", "chat"} <= set(cats)


def test_cloudflare_header():
    names, cats = detect_stack("<html></html>", {"server": "cloudflare"}, load_tech())
    assert "Cloudflare" in names and "cdn" in cats


def test_find_socials():
    html = (
        '<a href="https://www.linkedin.com/company/acme">in</a>'
        '<a href="https://twitter.com/share?u=1">share</a>'
        '<a href="https://www.dropbox.com/foo">box</a>'
        '<a href="https://github.com/acme">code</a>'
    )
    found = find_socials(html)
    assert found["LinkedIn"] == "https://linkedin.com/company/acme"
    assert found["GitHub"] == "https://github.com/acme"
    assert "X/Twitter" not in found


def test_detect_ats():
    html = '<a href="https://boards.greenhouse.io/acme">Jobs</a>'
    assert detect_ats(html, load_ats()) == ["Greenhouse"]


def test_analyze_site_offline(monkeypatch):
    home = (
        "<html><head><title>Acme</title>"
        '<meta name="description" content="We build things">'
        '<script src="https://js.hs-scripts.com/1.js"></script></head>'
        "<body><h1>Build faster</h1></body></html>"
    )
    careers = '<a href="https://boards.greenhouse.io/acme">Open roles</a>'
    pages = {
        "https://acme.com": FakeResponse(home, url="https://acme.com/"),
        "https://acme.com/careers": FakeResponse(careers, url="https://acme.com/careers"),
    }

    def fake_get(url, headers=None, retries=1):
        return pages.get(url, FakeResponse("", 404, url))

    monkeypatch.setattr("acr.analyze.get", fake_get)
    site = analyze_site("acme.com")
    assert site["title"] == "Acme"
    assert site["headline"] == "Build faster"
    assert "HubSpot" in site["stack"]
    assert site["pages"]["careers"] is True
    assert site["pages"]["pricing"] is False
    assert site["ats"] == ["Greenhouse"]


def test_analyze_site_unreachable(monkeypatch):
    monkeypatch.setattr("acr.analyze.get", lambda *a, **k: None)
    assert "error" in analyze_site("nowhere.example")
