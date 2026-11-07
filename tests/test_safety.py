import socket

import pytest
import requests

from acr import fetch, safety


def fake_dns(monkeypatch, table):
    """Make DNS resolve from a dict of hostname -> list of IPs; anything else fails."""

    def fake(host, port, *args, **kwargs):
        if host not in table:
            raise socket.gaierror("no such host")
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (ip, 0)) for ip in table[host]]

    monkeypatch.setattr(safety.socket, "getaddrinfo", fake)


@pytest.mark.parametrize(
    "ip",
    ["127.0.0.1", "10.1.2.3", "192.168.0.1", "169.254.169.254", "0.0.0.0", "100.64.0.1",
     "::1", "::ffff:127.0.0.1", "fe80::1"],
)
def test_private_ip_literals_are_blocked(ip):
    assert safety.host_is_public(ip) is False


def test_public_ip_literal_is_allowed():
    assert safety.host_is_public("8.8.8.8") is True


def test_hostname_resolving_publicly_is_allowed(monkeypatch):
    fake_dns(monkeypatch, {"acme.com": ["93.184.216.34"]})
    assert safety.host_is_public("acme.com") is True


def test_hostname_resolving_to_private_is_blocked(monkeypatch):
    fake_dns(
        monkeypatch,
        {"evil.example": ["10.0.0.5"], "mixed.example": ["93.184.216.34", "127.0.0.1"]},
    )
    assert safety.host_is_public("evil.example") is False
    assert safety.host_is_public("mixed.example") is False


def test_internal_names_are_blocked_even_if_they_resolve_publicly(monkeypatch):
    fake_dns(monkeypatch, {"localhost": ["93.184.216.34"], "db.internal": ["93.184.216.34"]})
    assert safety.host_is_public("localhost") is False
    assert safety.host_is_public("db.internal") is False


def test_unresolvable_and_malformed_hosts_are_blocked(monkeypatch):
    fake_dns(monkeypatch, {})
    for host in ["nope.example", "a..b.com", "-bad.com", "intranet", ""]:
        assert safety.host_is_public(host) is False, host


@pytest.mark.parametrize(
    "url,expected",
    [
        ("https://acme.com/pricing", True),
        ("https://acme.com:443/", True),
        ("ftp://acme.com/", False),
        ("https://acme.com:8443/", False),
        ("https://user:pw@acme.com/", False),
        ("http://169.254.169.254/latest/meta-data", False),
        ("https://", False),
    ],
)
def test_is_public_url(monkeypatch, url, expected):
    fake_dns(monkeypatch, {"acme.com": ["93.184.216.34"]})
    assert safety.is_public_url(url) is expected


def test_validate_domain_accepts_urls_and_cleans_them(monkeypatch):
    fake_dns(monkeypatch, {"acme.com": ["93.184.216.34"]})
    assert safety.validate_domain("https://www.Acme.com/pricing") == ("acme.com", None)


@pytest.mark.parametrize(
    "raw",
    ["", "   ", 123, "127.0.0.1", "localhost", "acme.com:8080", "evil@acme.com",
     "[::1]", "nodots", "x" * 400, "unresolved.example"],
)
def test_validate_domain_rejects_bad_input(monkeypatch, raw):
    fake_dns(monkeypatch, {"acme.com": ["93.184.216.34"]})
    domain, err = safety.validate_domain(raw)
    assert domain is None and err


def test_guard_blocks_before_any_request(monkeypatch):
    def boom(*args, **kwargs):
        raise AssertionError("the network must not be used")

    monkeypatch.setattr(fetch.requests, "get", boom)
    monkeypatch.setattr(fetch, "_url_guard", lambda url: False)
    assert fetch.get("https://acme.com") is None


class FakeRedirect:
    is_redirect = True
    url = "https://acme.com/"

    def __init__(self, location):
        self.headers = {"location": location}


def test_redirect_to_private_address_is_blocked(monkeypatch):
    monkeypatch.setattr(fetch, "_url_guard", safety.is_public_url)
    with pytest.raises(requests.exceptions.InvalidURL):
        fetch._check_redirect(FakeRedirect("http://169.254.169.254/latest/meta-data"))


def test_relative_redirect_on_public_host_is_allowed(monkeypatch):
    fake_dns(monkeypatch, {"acme.com": ["93.184.216.34"]})
    monkeypatch.setattr(fetch, "_url_guard", safety.is_public_url)
    response = FakeRedirect("/pricing")
    assert fetch._check_redirect(response) is response
