"""Load technology and hiring-platform signatures from the YAML files in acr/data/."""

from pathlib import Path

import yaml

DATA = Path(__file__).parent / "data"


def _load(name):
    return yaml.safe_load((DATA / name).read_text(encoding="utf-8")) or []


def load_tech():
    """Return a list of dicts with the keys: name, category, signatures."""
    return _load("tech.yml")


def load_ats():
    """Return a dict mapping hiring platform name to a URL fragment."""
    return {item["name"]: item["signature"] for item in _load("ats.yml")}
