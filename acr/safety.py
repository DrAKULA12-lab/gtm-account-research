"""Network safety checks for running acr as a tool for AI agents (SSRF guard).

An agent can be tricked by text it reads (prompt injection) into asking for
http://169.254.169.254 or an internal hostname. These checks make sure acr only
talks to public internet hosts when it is driven by an agent.
"""

import ipaddress
import re
import socket
from urllib.parse import urlparse

from acr.analyze import clean_domain

_LABEL = r"(?!-)[a-z0-9-]{1,63}(?<!-)"
_HOSTNAME = re.compile(rf"^{_LABEL}(\.{_LABEL})+$")
_BLOCKED_SUFFIXES = (".local", ".localhost", ".internal", ".lan", ".home", ".corp", ".intranet")


def _is_ip(text):
    try:
        ipaddress.ip_address(text.split("%")[0])
    except ValueError:
        return False
    return True


def _ip_is_public(text):
    try:
        ip = ipaddress.ip_address(text.split("%")[0])
    except ValueError:
        return False
    if ip.version == 6 and ip.ipv4_mapped is not None:
        ip = ip.ipv4_mapped
    return ip.is_global


def host_is_public(host):
    """True for a public IP, or a hostname whose every address is a public IP."""
    host = host.strip().strip("[]").lower().rstrip(".")
    if not host or len(host) > 253:
        return False
    if _is_ip(host):
        return _ip_is_public(host)
    if host == "localhost" or host.endswith(_BLOCKED_SUFFIXES):
        return False
    if not _HOSTNAME.match(host):
        return False
    try:
        infos = socket.getaddrinfo(host, None, proto=socket.IPPROTO_TCP)
    except (socket.gaierror, UnicodeError, OSError):
        return False
    addresses = {info[4][0] for info in infos}
    return bool(addresses) and all(_ip_is_public(a) for a in addresses)


def is_public_url(url):
    """True if url is http(s) on a standard port, has no credentials, and targets a public host."""
    try:
        p = urlparse(url)
        port = p.port
    except ValueError:
        return False
    if p.scheme not in ("http", "https") or not p.hostname:
        return False
    if port not in (None, 80, 443):
        return False
    if p.username or p.password:
        return False
    return host_is_public(p.hostname)


def validate_domain(raw):
    """Return (domain, error) for a company domain or URL supplied by an agent."""
    if not isinstance(raw, str) or not raw.strip():
        return None, "domain must be a non-empty string"
    if len(raw) > 300:
        return None, "domain is too long"
    try:
        domain = clean_domain(raw)
    except ValueError:
        return None, "not a valid domain name"
    if "@" in domain or ":" in domain:
        return None, "domain must not include credentials or a port"
    if _is_ip(domain):
        return None, "use a company domain name, not an IP address"
    if "." not in domain or len(domain) > 253 or not _HOSTNAME.match(domain):
        return None, "not a valid domain name"
    if not host_is_public(domain):
        return None, f"'{domain}' is not a public internet host"
    return domain, None
