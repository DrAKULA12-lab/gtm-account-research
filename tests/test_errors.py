import pytest
import requests

from acr import analyze, fetch


@pytest.mark.parametrize(
    "exc, words",
    [
        (requests.exceptions.ConnectTimeout("t"), "timed out"),
        (requests.exceptions.SSLError("s"), "SSL certificate"),
        (requests.exceptions.ConnectionError("c"), "could not connect"),
        (requests.exceptions.TooManyRedirects("r"), "too many redirects"),
    ],
)
def test_unreachable_site_explains_why(monkeypatch, exc, words):
    def boom(*args, **kwargs):
        raise exc

    monkeypatch.setattr(fetch.requests, "get", boom)
    monkeypatch.setattr(fetch, "_url_guard", None, raising=False)
    result = analyze.analyze_site("example.com")
    assert result["error"].startswith("Could not reach example.com (")
    assert words in result["error"]


def test_guard_block_is_explained(monkeypatch):
    monkeypatch.setattr(fetch, "_url_guard", lambda url: False, raising=False)
    result = analyze.analyze_site("example.com")
    assert "safety guard" in result["error"]
