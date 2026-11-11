import pytest

from acr import github


@pytest.mark.parametrize(
    "name", ["", "../x", "a b", "org?x=1", "-bad", "x" * 40, None, "a/b"]
)
def test_bad_github_names_are_rejected_without_a_request(monkeypatch, name):
    def boom(*args, **kwargs):
        raise AssertionError("no request should be made")

    monkeypatch.setattr(github, "get", boom)
    assert "error" in github.github_info(name)
