import pytest


@pytest.fixture(autouse=True)
def _isolated_cache(tmp_path, monkeypatch):
    monkeypatch.setenv("ACR_CACHE_DIR", str(tmp_path / "cache"))
    monkeypatch.delenv("ACR_NO_CACHE", raising=False)
    monkeypatch.delenv("ACR_CACHE_TTL", raising=False)
