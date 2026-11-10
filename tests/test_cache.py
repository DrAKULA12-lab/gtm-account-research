import requests

from acr import cache, fetch

URL = "https://example.com/"


def make_response(body=b"<html>hello</html>"):
    r = requests.Response()
    r.status_code = 200
    r.url = URL
    r.headers["content-type"] = "text/html; charset=utf-8"
    r.encoding = "utf-8"
    r._content = body
    return r


def test_roundtrip():
    cache.save(URL, make_response())
    hit = cache.load(URL)
    assert hit is not None
    assert hit.status_code == 200
    assert "hello" in hit.text


def test_miss_when_empty():
    assert cache.load("https://nothing.example/") is None


def test_expired_entry_is_ignored(monkeypatch):
    cache.save(URL, make_response())
    monkeypatch.setenv("ACR_CACHE_TTL", "-1")
    assert cache.load(URL) is None


def test_disabled_by_env(monkeypatch):
    monkeypatch.setenv("ACR_NO_CACHE", "1")
    cache.save(URL, make_response())
    assert cache.load(URL) is None


def _count_calls(monkeypatch):
    calls = []

    def fake_network(url, headers=None, retries=1):
        calls.append(url)
        return make_response()

    monkeypatch.setattr(fetch, "_get_network", fake_network)
    monkeypatch.setattr(fetch, "_url_guard", None, raising=False)
    return calls


def test_get_uses_cache_the_second_time(monkeypatch):
    calls = _count_calls(monkeypatch)
    assert fetch.get(URL).status_code == 200
    assert fetch.get(URL).status_code == 200
    assert len(calls) == 1


def test_get_skips_cache_for_authorized_requests(monkeypatch):
    calls = _count_calls(monkeypatch)
    fetch.get(URL, headers={"Authorization": "token x"})
    fetch.get(URL, headers={"Authorization": "token x"})
    assert len(calls) == 2
